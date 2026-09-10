from dataclasses import dataclass
from functools import wraps
from inspect import signature
from typing import Any

from backend.app.core.passwords import hash_password, verify_password
from backend.app.core.security import create_access_token
from backend.app.modules.vertical_slice.domain import (
    LEVEL_XP_REQUIREMENT,
    AccountRecord,
    CharacterRecord,
    FightResult,
)
from backend.app.modules.vertical_slice.store import VerticalSliceStore

STARTER_QUEST_KEY = "lantern_well_first_light"
STARTER_ENEMY_KEY = "fog_thorn_lurker"
STARTER_ITEM_REWARD = "sunthread_bandage"
STARTER_CURRENCY_KEY = "shell_chits"
STARTER_QUEST_CURRENCY_REWARD = 12

SPELL_DAMAGE = {
    "glimmer_spark": 14,
    "root_snare": 12,
    "tide_mend": 0,
}

ENEMY_VIGOR = {
    STARTER_ENEMY_KEY: 12,
}


class VerticalSliceError(ValueError):
    pass


class AuthenticationError(VerticalSliceError):
    pass


class NotFoundError(VerticalSliceError):
    pass


@dataclass(frozen=True)
class AuthResult:
    account: AccountRecord
    access_token: str

    def public_state(self) -> dict[str, Any]:
        return {
            "account": {
                "id": self.account.id,
                "email": self.account.email,
                "display_name": self.account.display_name,
            },
            "access_token": self.access_token,
        }


def atomic(fn):
    sig = signature(fn)
    @wraps(fn)
    def wrapped(self, *args, **kwargs):
        bound = sig.bind(self, *args, **kwargs)
        with self.store.transaction(bound.arguments.get("character_id")):
            return fn(self, *args, **kwargs)
    return wrapped


class VerticalSliceService:
    def __init__(self, store: VerticalSliceStore, quest_rules=None) -> None:
        self.store = store
        self.quest_rules = quest_rules

    @atomic
    def register(self, email: str, display_name: str, password: str) -> AuthResult:
        normalized_email = _normalize_email(email)
        if "@" not in normalized_email or len(normalized_email) > 254:
            raise VerticalSliceError("email is required")
        if not 8 <= len(password) <= 128:
            raise VerticalSliceError("password must be at least 8 characters")
        if self.store.get_account_by_email(normalized_email):
            raise VerticalSliceError("account already exists")

        account = AccountRecord.create(
            email=normalized_email,
            display_name=display_name.strip(),
            password_hash=hash_password(password),
        )
        self.store.save_account(account)
        return self._auth_result(account)

    @atomic
    def login(self, email: str, password: str) -> AuthResult:
        account = self.store.get_account_by_email(_normalize_email(email))
        if account is None or not verify_password(password, account.password_hash):
            raise AuthenticationError("invalid email or password")
        if not account.password_hash.startswith("$argon2"):
            account.password_hash = hash_password(password)
            self.store.save_account(account)
        return self._auth_result(account)

    @atomic
    def create_character(
        self,
        account_id: str,
        name: str,
        ancestry_key: str = "lumenfolk",
        origin_key: str = "dawnreef_local",
        affinity: str = "lanterncraft",
        appearance: dict[str, str] | None = None,
    ) -> CharacterRecord:
        self._require_account(account_id)
        if self.store.list_characters(account_id):
            raise VerticalSliceError("vertical slice supports one character per account")

        if not 2 <= len(name.strip()) <= 24 or not all(c.isalnum() or c in " '-" for c in name):
            raise VerticalSliceError("name must contain 2–24 letters, numbers, spaces, apostrophes or hyphens")
        if affinity not in {"lanterncraft", "rootbinding", "tideseaming"}:
            raise VerticalSliceError("unknown affinity")
        appearance = appearance or {"robe": "teal", "skin": "warm"}
        if set(appearance) != {"robe", "skin"} or appearance["robe"] not in {"teal", "coral", "indigo"} or appearance["skin"] not in {"warm", "deep", "pale"}:
            raise VerticalSliceError("unknown appearance preset")
        character = CharacterRecord.create(
            account_id=account_id,
            name=name.strip(),
            ancestry_key=ancestry_key,
            origin_key=origin_key,
        )
        character.affinity = affinity
        character.appearance = dict(appearance)
        character.inventory[STARTER_ITEM_REWARD] = 1
        character.wallet[STARTER_CURRENCY_KEY] = 0
        self.store.save_character(character)
        return character

    def list_characters(self, account_id: str) -> list[CharacterRecord]:
        self._require_account(account_id)
        return self.store.list_characters(account_id)

    def enter_world(self, account_id: str, character_id: str) -> CharacterRecord:
        return self._require_character(account_id, character_id)

    @atomic
    def accept_quest(self, account_id: str, character_id: str, quest_key: str) -> CharacterRecord:
        if quest_key != STARTER_QUEST_KEY:
            raise NotFoundError("quest is not available in the vertical slice")
        character = self._require_character(account_id, character_id)
        if self.quest_rules:
            # Preserve the existing starter-only API; later quests come from NPC dialogue.
            self.quest_rules.accept(character, quest_key, "mara_lanternwright")
            self.store.save_character(character)
            return character
        character.quest_state.setdefault(
            quest_key,
            {
                "state": "accepted",
                "objectives": {"defeat_fog_thorn_lurker": 0},
                "completed": False,
                "rewards_claimed": False,
            },
        )
        self.store.save_character(character)
        return character

    @atomic
    def fight_enemy(
        self,
        account_id: str,
        character_id: str,
        enemy_key: str,
        spell_key: str,
    ) -> FightResult:
        if enemy_key != STARTER_ENEMY_KEY:
            raise NotFoundError("enemy is not available in the vertical slice")
        character = self._require_character(account_id, character_id)
        if spell_key not in character.known_spells:
            raise VerticalSliceError("character does not know that spell")

        if character.encounter.get("state") == "active":
            raise VerticalSliceError("finish the active encounter first")
        if character.defeated_enemies.get(enemy_key, 0):
            return FightResult(character, enemy_key, spell_key, True, 0, False, None, {"items": {}, "currency": {}, "quest": None})
        damage = SPELL_DAMAGE.get(spell_key, 0)
        if spell_key == "tide_mend":
            character.vigor = min(character.vigor + 8, 30)
            damage = 0

        victory = damage >= ENEMY_VIGOR[enemy_key]
        experience_gained = 0
        rewards: dict[str, Any] = {"items": {}, "currency": {}, "quest": None}
        completed_quest: str | None = None
        level_gained = False

        if victory:
            character.defeated_enemies[enemy_key] = character.defeated_enemies.get(enemy_key, 0) + 1
            experience_gained += 25
            rewards["currency"][STARTER_CURRENCY_KEY] = 2
            character.wallet[STARTER_CURRENCY_KEY] = character.wallet.get(STARTER_CURRENCY_KEY, 0) + 2

            quest = character.quest_state.get(STARTER_QUEST_KEY)
            if quest and not quest.get("completed"):
                quest["objectives"]["defeat_fog_thorn_lurker"] = 1
                quest["state"] = "completed"
                quest["completed"] = True
                quest["rewards_claimed"] = True
                completed_quest = STARTER_QUEST_KEY
                rewards["quest"] = STARTER_QUEST_KEY
                rewards["items"][STARTER_ITEM_REWARD] = 1
                rewards["currency"][STARTER_CURRENCY_KEY] = (
                    rewards["currency"].get(STARTER_CURRENCY_KEY, 0)
                    + STARTER_QUEST_CURRENCY_REWARD
                )
                character.inventory[STARTER_ITEM_REWARD] = (
                    character.inventory.get(STARTER_ITEM_REWARD, 0) + 1
                )
                character.wallet[STARTER_CURRENCY_KEY] = (
                    character.wallet.get(STARTER_CURRENCY_KEY, 0)
                    + STARTER_QUEST_CURRENCY_REWARD
                )
                experience_gained += 75

        if experience_gained:
            character.experience += experience_gained
            while character.experience >= LEVEL_XP_REQUIREMENT * character.level:
                character.level += 1
                level_gained = True

        self.store.save_character(character)
        return FightResult(
            character=character,
            enemy_key=enemy_key,
            spell_key=spell_key,
            victory=victory,
            experience_gained=experience_gained,
            level_gained=level_gained,
            quest_completed=completed_quest,
            rewards=rewards,
        )

    @atomic
    def save_progress(self, account_id: str, character_id: str) -> CharacterRecord:
        character = self._require_character(account_id, character_id)
        self.store.save_character(character)
        self.store.flush()
        return character

    @atomic
    def logout(self, account_id: str) -> dict[str, str]:
        account = self._require_account(account_id)
        account.auth_version += 1
        self.store.save_account(account)
        self.store.flush()
        return {"status": "logged_out"}

    def _auth_result(self, account: AccountRecord) -> AuthResult:
        return AuthResult(
            account=account,
            access_token=create_access_token(account.id, {"type": "access", "session_version": account.auth_version}),
        )

    def validate_session(self, payload: dict) -> str:
        account = self._require_account(str(payload.get("sub", "")))
        if payload.get("type") != "access" or payload.get("session_version", 0) != account.auth_version:
            raise AuthenticationError("session expired; sign in again")
        return account.id

    def _require_account(self, account_id: str) -> AccountRecord:
        account = self.store.get_account(account_id)
        if account is None:
            raise AuthenticationError("account not found")
        return account

    def _require_character(self, account_id: str, character_id: str) -> CharacterRecord:
        character = self.store.get_character(character_id)
        if character is None:
            raise NotFoundError("character not found")
        if character.account_id != account_id:
            raise AuthenticationError("character does not belong to account")
        return character


def _normalize_email(email: str) -> str:
    return email.strip().lower()

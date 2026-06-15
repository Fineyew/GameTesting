from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

STARTING_ZONE_KEY = "dawnreef_atoll"
STARTING_SPELL_KEYS = ("glimmer_spark", "root_snare", "tide_mend")
LEVEL_XP_REQUIREMENT = 100
STARTING_VIGOR = 30


@dataclass
class AccountRecord:
    id: str
    email: str
    display_name: str
    password_hash: str

    @classmethod
    def create(cls, email: str, display_name: str, password_hash: str) -> "AccountRecord":
        return cls(
            id=str(uuid4()),
            email=email,
            display_name=display_name,
            password_hash=password_hash,
        )


@dataclass
class CharacterRecord:
    id: str
    account_id: str
    name: str
    ancestry_key: str
    origin_key: str
    level: int = 1
    experience: int = 0
    current_zone_key: str = STARTING_ZONE_KEY
    vigor: int = STARTING_VIGOR
    known_spells: list[str] = field(default_factory=lambda: list(STARTING_SPELL_KEYS))
    inventory: dict[str, int] = field(default_factory=dict)
    wallet: dict[str, int] = field(default_factory=dict)
    quest_state: dict[str, dict[str, Any]] = field(default_factory=dict)
    defeated_enemies: dict[str, int] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        account_id: str,
        name: str,
        ancestry_key: str,
        origin_key: str,
    ) -> "CharacterRecord":
        return cls(
            id=str(uuid4()),
            account_id=account_id,
            name=name,
            ancestry_key=ancestry_key,
            origin_key=origin_key,
        )

    def public_state(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FightResult:
    character: CharacterRecord
    enemy_key: str
    spell_key: str
    victory: bool
    experience_gained: int
    level_gained: bool
    quest_completed: str | None
    rewards: dict[str, Any]

    def public_state(self) -> dict[str, Any]:
        return {
            "character": self.character.public_state(),
            "enemy_key": self.enemy_key,
            "spell_key": self.spell_key,
            "victory": self.victory,
            "experience_gained": self.experience_gained,
            "level_gained": self.level_gained,
            "quest_completed": self.quest_completed,
            "rewards": self.rewards,
        }

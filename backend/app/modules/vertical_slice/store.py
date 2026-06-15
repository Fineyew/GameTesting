import json
from copy import deepcopy
from pathlib import Path
from typing import Protocol

from backend.app.modules.vertical_slice.domain import AccountRecord, CharacterRecord


class VerticalSliceStore(Protocol):
    def save_account(self, account: AccountRecord) -> None:
        raise NotImplementedError

    def get_account(self, account_id: str) -> AccountRecord | None:
        raise NotImplementedError

    def get_account_by_email(self, email: str) -> AccountRecord | None:
        raise NotImplementedError

    def save_character(self, character: CharacterRecord) -> None:
        raise NotImplementedError

    def get_character(self, character_id: str) -> CharacterRecord | None:
        raise NotImplementedError

    def list_characters(self, account_id: str) -> list[CharacterRecord]:
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError


class InMemoryVerticalSliceStore:
    def __init__(self) -> None:
        self.accounts: dict[str, AccountRecord] = {}
        self.characters: dict[str, CharacterRecord] = {}

    def save_account(self, account: AccountRecord) -> None:
        self.accounts[account.id] = deepcopy(account)

    def get_account(self, account_id: str) -> AccountRecord | None:
        account = self.accounts.get(account_id)
        return deepcopy(account) if account else None

    def get_account_by_email(self, email: str) -> AccountRecord | None:
        normalized = email.strip().lower()
        for account in self.accounts.values():
            if account.email == normalized:
                return deepcopy(account)
        return None

    def save_character(self, character: CharacterRecord) -> None:
        self.characters[character.id] = deepcopy(character)

    def get_character(self, character_id: str) -> CharacterRecord | None:
        character = self.characters.get(character_id)
        return deepcopy(character) if character else None

    def list_characters(self, account_id: str) -> list[CharacterRecord]:
        return [
            deepcopy(character)
            for character in self.characters.values()
            if character.account_id == account_id
        ]

    def flush(self) -> None:
        return None


class JsonVerticalSliceStore(InMemoryVerticalSliceStore):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__()
        self._load()

    def save_account(self, account: AccountRecord) -> None:
        super().save_account(account)
        self.flush()

    def save_character(self, character: CharacterRecord) -> None:
        super().save_character(character)
        self.flush()

    def flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "accounts": [account.__dict__ for account in self.accounts.values()],
            "characters": [character.__dict__ for character in self.characters.values()],
        }
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary_path.replace(self.path)

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.accounts = {
            account["id"]: AccountRecord(**account)
            for account in payload.get("accounts", [])
        }
        self.characters = {
            character["id"]: CharacterRecord(**character)
            for character in payload.get("characters", [])
        }

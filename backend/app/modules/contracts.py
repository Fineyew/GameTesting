from typing import Any, Protocol
from uuid import UUID

from backend.app.core.events import DomainEvent


class ContentReader(Protocol):
    """Read-only content access used by gameplay modules."""

    def get_definition(self, content_type: str, key: str) -> Any:
        raise NotImplementedError

    def list_definitions(self, content_type: str | None = None) -> list[Any]:
        raise NotImplementedError


class EventPublisher(Protocol):
    """Boundary for emitting cross-module facts without direct imports."""

    async def publish(self, event: DomainEvent) -> None:
        raise NotImplementedError


class InventoryGrantPort(Protocol):
    """Minimal inventory command surface for rewards."""

    async def grant_item(
        self,
        character_id: UUID,
        item_key: str,
        quantity: int,
        source: str,
        idempotency_key: str,
    ) -> None:
        raise NotImplementedError

    async def grant_currency(
        self,
        character_id: UUID,
        currency_key: str,
        amount: int,
        source: str,
        idempotency_key: str,
    ) -> None:
        raise NotImplementedError

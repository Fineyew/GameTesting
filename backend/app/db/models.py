from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class Character(TimestampMixin, Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    ancestry_key: Mapped[str] = mapped_column(String(128), nullable=False)
    origin_key: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    experience: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    current_zone_key: Mapped[str | None] = mapped_column(String(128))
    position: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    stats: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    flags: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class ContentDefinition(TimestampMixin, Base):
    __tablename__ = "content_definitions"
    __table_args__ = (
        UniqueConstraint("type", "key", "version", "locale", name="uq_content_definition_version"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    locale: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False)


class ItemInstance(TimestampMixin, Base):
    __tablename__ = "item_instances"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    character_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id"),
        nullable=False,
    )
    item_key: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    durability: Mapped[int | None] = mapped_column(Integer)
    bound_state: Mapped[str] = mapped_column(String(32), default="unbound", nullable=False)
    instance_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class CharacterQuest(Base):
    __tablename__ = "character_quests"

    character_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id"),
        primary_key=True,
    )
    quest_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    objective_state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CombatSession(TimestampMixin, Base):
    __tablename__ = "combat_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_character_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("characters.id"))
    party_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    encounter_key: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    participants: Mapped[dict] = mapped_column(JSONB, nullable=False)
    action_log: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    rewards: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(128), nullable=False)
    sender_character_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("characters.id"))
    body: Mapped[str] = mapped_column(String(500), nullable=False)
    moderation_state: Mapped[str] = mapped_column(String(32), default="visible", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

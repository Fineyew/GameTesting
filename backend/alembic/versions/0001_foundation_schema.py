"""foundation schema

Revision ID: 0001_foundation_schema
Revises:
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_foundation_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=64), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "content_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("definition", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_content_definitions_version_min"),
        sa.UniqueConstraint("type", "key", "version", "locale", name="uq_content_definition_version"),
    )
    op.create_index(
        "idx_content_definitions_lookup",
        "content_definitions",
        ["type", "key", "status", "version"],
    )

    op.create_table(
        "characters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False, unique=True),
        sa.Column("ancestry_key", sa.String(length=128), nullable=False),
        sa.Column("origin_key", sa.String(length=128), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("experience", sa.BigInteger(), nullable=False),
        sa.Column("current_zone_key", sa.String(length=128)),
        sa.Column("position", postgresql.JSONB(), nullable=False),
        sa.Column("stats", postgresql.JSONB(), nullable=False),
        sa.Column("flags", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("level >= 1", name="ck_characters_level_min"),
        sa.CheckConstraint("experience >= 0", name="ck_characters_experience_min"),
    )
    op.create_index("idx_characters_account_id", "characters", ["account_id"])

    op.create_table(
        "item_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("character_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("item_key", sa.String(length=128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("durability", sa.Integer()),
        sa.Column("bound_state", sa.String(length=32), nullable=False),
        sa.Column("instance_data", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity >= 0", name="ck_item_instances_quantity_min"),
    )
    op.create_index("idx_item_instances_character_id", "item_instances", ["character_id"])

    op.create_table(
        "character_quests",
        sa.Column("character_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("characters.id"), primary_key=True),
        sa.Column("quest_key", sa.String(length=128), primary_key=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("objective_state", postgresql.JSONB(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "combat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_character_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("characters.id")),
        sa.Column("party_id", postgresql.UUID(as_uuid=True)),
        sa.Column("encounter_key", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("participants", postgresql.JSONB(), nullable=False),
        sa.Column("action_log", postgresql.JSONB(), nullable=False),
        sa.Column("rewards", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("round_number >= 1", name="ck_combat_sessions_round_min"),
    )
    op.create_index(
        "idx_combat_sessions_owner_state",
        "combat_sessions",
        ["owner_character_id", "state"],
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column("channel_id", sa.String(length=128), nullable=False),
        sa.Column("sender_character_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("characters.id")),
        sa.Column("body", sa.String(length=500), nullable=False),
        sa.Column("moderation_state", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_chat_messages_channel_created",
        "chat_messages",
        ["channel_type", "channel_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_chat_messages_channel_created", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("idx_combat_sessions_owner_state", table_name="combat_sessions")
    op.drop_table("combat_sessions")
    op.drop_table("character_quests")
    op.drop_index("idx_item_instances_character_id", table_name="item_instances")
    op.drop_table("item_instances")
    op.drop_index("idx_characters_account_id", table_name="characters")
    op.drop_table("characters")
    op.drop_index("idx_content_definitions_lookup", table_name="content_definitions")
    op.drop_table("content_definitions")
    op.drop_table("accounts")

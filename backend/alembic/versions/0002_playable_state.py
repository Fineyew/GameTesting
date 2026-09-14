"""Persist the playable aggregate without discarding foundation tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "0002_playable_state"
down_revision = "0001_foundation_schema"
branch_labels = depends_on = None


def upgrade():
    op.add_column("accounts", sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0"))
    op.create_table("character_runtime_states",
                    sa.Column("character_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("characters.id"), primary_key=True),
                    sa.Column("schema_version", sa.Integer(), nullable=False),
                    sa.Column("payload", postgresql.JSONB(), nullable=False))


def downgrade():
    op.drop_table("character_runtime_states")
    op.drop_column("accounts", "auth_version")

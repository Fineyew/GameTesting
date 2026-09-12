"""PostgreSQL adapter. One character aggregate and its receipts commit together."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict
from uuid import UUID
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from backend.app.db.models import Account, Character, CharacterRuntimeState
from backend.app.modules.vertical_slice.domain import AccountRecord, CharacterRecord


class PostgresPlayerStore:
    def __init__(self, url):
        self.engine = create_engine(url.replace("+asyncpg", "+psycopg"), pool_size=3, max_overflow=2, pool_pre_ping=True)
        self._current = ContextVar("player_transaction", default=None)

    @contextmanager
    def transaction(self, character_id=None):
        if self._current.get() is not None:
            yield
            return
        with Session(self.engine) as session, session.begin():
            session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": character_id or "identity"})
            token = self._current.set(session)
            try:
                yield
            finally:
                self._current.reset(token)

    @contextmanager
    def _session(self):
        with self.transaction():
            yield self._current.get()

    def get_account(self, account_id):
        try:
            identity = UUID(account_id)
        except (ValueError, TypeError):
            return None
        with self._session() as session:
            return self._account(session.get(Account, identity))

    def get_account_by_email(self, email):
        with self._session() as session:
            return self._account(session.scalar(select(Account).where(Account.email == email.strip().lower())))

    @staticmethod
    def _account(row):
        if row is None or row.status != "active":
            return None
        return AccountRecord(str(row.id), row.email, row.display_name, row.password_hash, row.auth_version)

    def save_account(self, record):
        with self._session() as session:
            row = session.get(Account, UUID(record.id))
            if row is None:
                row = Account(id=UUID(record.id), status="active")
                session.add(row)
            row.email, row.display_name, row.password_hash, row.auth_version = record.email, record.display_name, record.password_hash, record.auth_version
            session.flush()

    def get_character(self, character_id):
        try:
            identity = UUID(character_id)
        except (ValueError, TypeError):
            return None
        with self._session() as session:
            row = session.get(CharacterRuntimeState, identity)
            if row is None:
                return None
            if row.schema_version != 1:
                raise ValueError("unsupported character schema")
            return CharacterRecord(**row.payload)

    def list_characters(self, account_id):
        with self._session() as session:
            rows = session.scalars(select(CharacterRuntimeState).join(Character).where(Character.account_id == UUID(account_id)))
            return [CharacterRecord(**row.payload) for row in rows]

    def save_character(self, record):
        with self._session() as session:
            identity = UUID(record.id)
            row = session.get(Character, identity)
            if row is None:
                row = Character(id=identity, account_id=UUID(record.account_id), flags={})
                session.add(row)
            for name in ("name", "ancestry_key", "origin_key", "level", "experience", "current_zone_key", "position"):
                setattr(row, name, getattr(record, name))
            row.stats = {"vigor": record.vigor}
            session.flush()
            state = session.get(CharacterRuntimeState, identity)
            if state is None:
                state = CharacterRuntimeState(character_id=identity, schema_version=1)
                session.add(state)
            state.payload = asdict(record)
            session.flush()

    def flush(self):
        pass

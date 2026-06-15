import unittest

from backend.app.core.config import Settings, validate_runtime_settings
from backend.app.core.security import create_access_token


class RuntimeConfigTests(unittest.TestCase):
    def test_production_rejects_placeholder_jwt_secret(self) -> None:
        settings = Settings(
            environment="production",
            jwt_secret="change-this-jwt-secret-with-enough-length",
            database_url="postgresql+asyncpg://prod_user:strong-database-password@db:5432/game",
        )

        with self.assertRaisesRegex(RuntimeError, "placeholder"):
            validate_runtime_settings(settings)

    def test_production_rejects_scaffold_database_username(self) -> None:
        settings = Settings(
            environment="production",
            jwt_secret="a-realistic-jwt-signing-key-with-32-chars",
            database_url="postgresql+asyncpg://game:strong-database-password@db:5432/game",
        )

        with self.assertRaisesRegex(RuntimeError, "scaffold database username"):
            validate_runtime_settings(settings)

    def test_production_accepts_non_placeholder_secrets(self) -> None:
        settings = Settings(
            environment="production",
            jwt_secret="a-realistic-jwt-signing-key-with-32-chars",
            database_url="postgresql+asyncpg://prod_user:strong-db-passphrase-32-chars@db:5432/game",
        )

        validate_runtime_settings(settings)


class JwtSecurityTests(unittest.TestCase):
    def test_extra_claims_cannot_override_reserved_claims(self) -> None:
        with self.assertRaisesRegex(ValueError, "reserved JWT claims"):
            create_access_token("account-id", {"sub": "other-account"})

    def test_extra_claims_can_add_non_reserved_claims(self) -> None:
        token = create_access_token("account-id", {"role": "tester"})
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)


if __name__ == "__main__":
    unittest.main()

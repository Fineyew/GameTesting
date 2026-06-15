import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.core.config import get_settings

RESERVED_JWT_CLAIMS = frozenset({"sub", "iss", "aud", "iat", "exp", "nbf", "jti"})


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    if extra_claims:
        reserved = RESERVED_JWT_CLAIMS.intersection(extra_claims)
        if reserved:
            reserved_list = ", ".join(sorted(reserved))
            raise ValueError(f"extra_claims cannot override reserved JWT claims: {reserved_list}")

    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_token_minutes)).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return _encode_hs256(payload, settings.jwt_secret)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        header_raw, payload_raw, signature_raw = token.split(".", 2)
        signing_input = f"{header_raw}.{payload_raw}"
        expected_signature = _base64url(
            hmac.new(
                settings.jwt_secret.encode("utf-8"),
                signing_input.encode("utf-8"),
                hashlib.sha256,
            ).digest()
        )
        if not hmac.compare_digest(signature_raw, expected_signature):
            raise ValueError("invalid token signature")

        header = _base64url_json_decode(header_raw)
        payload = _base64url_json_decode(payload_raw)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("invalid access token") from exc

    if header.get("alg") != "HS256":
        raise ValueError("unsupported token algorithm")
    if payload.get("iss") != settings.jwt_issuer:
        raise ValueError("invalid token issuer")
    if payload.get("aud") != settings.jwt_audience:
        raise ValueError("invalid token audience")
    if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
        raise ValueError("access token expired")
    return payload


def _encode_hs256(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        [
            _base64url_json(header),
            _base64url_json(payload),
        ]
    )
    signature = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url(signature)}"


def _base64url_json(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _base64url(encoded)


def _base64url(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _base64url_json_decode(payload: str) -> dict[str, Any]:
    padding = "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(payload + padding)
    parsed = json.loads(decoded)
    if not isinstance(parsed, dict):
        raise ValueError("JWT section must be an object")
    return parsed

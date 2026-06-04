from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings


ALGORITHM = "HS256"
ISSUER = "autonomous-research-agent"


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    return pwd_context.verify(
        plain_password,
        password_hash,
    )


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()

    now = datetime.now(UTC)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iss": ISSUER,
        "iat": now,
        "nbf": now,
        "exp": now
        + timedelta(
            minutes=settings.access_token_expire_minutes,
        ),
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def create_refresh_token(subject: str) -> str:
    settings = get_settings()

    now = datetime.now(UTC)

    payload = {
        "sub": subject,
        "type": "refresh",
        "iss": ISSUER,
        "iat": now,
        "nbf": now,
        "exp": now
        + timedelta(
            minutes=settings.refresh_token_expire_minutes,
        ),
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_nbf": True,
                "verify_iss": True,
                "require_sub": True,
                "require_exp": True,
                "require_iat": True,
                "require_nbf": True,
                "require_iss": True,
            },
        )

        token_type = payload.get("type")

        if token_type not in {
            "access",
            "refresh",
        }:
            raise ValueError(
                "Invalid token type"
            )

        return payload

    except JWTError as exc:
        raise ValueError(
            "Invalid authentication token"
        ) from exc


def decode_access_token(
    token: str,
) -> dict[str, Any]:
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise ValueError(
            "Expected access token"
        )

    return payload


def decode_refresh_token(
    token: str,
) -> dict[str, Any]:
    payload = decode_token(token)

    if payload.get("type") != "refresh":
        raise ValueError(
            "Expected refresh token"
        )

    return payload
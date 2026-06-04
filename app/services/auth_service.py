from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthenticationError(ValueError):
    pass


class DuplicateUserError(ValueError):
    pass


class RegistrationError(ValueError):
    pass


class AuthService:
    DEFAULT_REGISTRATION_ROLE = "researcher"

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def register(
        self,
        request: RegisterRequest,
    ) -> User:
        email = request.email.lower().strip()

        existing = await self.users.get_by_email(email)

        if existing:
            raise DuplicateUserError("A user with this email already exists")

        role = self._resolve_registration_role(request)

        user = await self.users.create(
            name=request.name.strip(),
            email=email,
            password_hash=hash_password(request.password),
            role=role,
        )

        await self.session.commit()

        return user

    async def login(
        self,
        request: LoginRequest,
    ) -> TokenResponse:
        email = request.email.lower().strip()

        user = await self.users.get_by_email(email)

        if user is None or not verify_password(
            request.password,
            user.password_hash,
        ):
            raise AuthenticationError("Invalid email or password")

        access_token = create_access_token(
            user.id,
            {
                "role": user.role,
                "email": user.email,
            },
        )

        refresh_token = create_refresh_token(
            user.id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def _resolve_registration_role(
        self,
        request: RegisterRequest,
    ) -> str:
        requested_role = request.role.lower().strip() if request.role else self.DEFAULT_REGISTRATION_ROLE

        allowed_public_roles = {
            "researcher",
            "viewer",
        }

        if requested_role not in allowed_public_roles:
            return self.DEFAULT_REGISTRATION_ROLE

        return requested_role

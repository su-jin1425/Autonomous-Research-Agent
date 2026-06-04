from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthenticationError(ValueError):
    pass


class DuplicateUserError(ValueError):
    pass


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def register(self, request: RegisterRequest) -> User:
        existing = await self.users.get_by_email(request.email)
        if existing:
            raise DuplicateUserError("A user with this email already exists")
        user = await self.users.create(
            name=request.name,
            email=request.email,
            password_hash=hash_password(request.password),
            role=request.role,
        )
        await self.session.commit()
        return user

    async def login(self, request: LoginRequest) -> TokenResponse:
        user = await self.users.get_by_email(request.email)
        if user is None or not verify_password(request.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        return TokenResponse(
            access_token=create_access_token(user.id, {"role": user.role}),
            refresh_token=create_refresh_token(user.id),
        )


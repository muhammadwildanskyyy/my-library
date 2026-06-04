"""
Authentication service — register and login business logic.
"""

from uuid import UUID

from app.config.security import create_access_token, hash_password, verify_password
from app.domain.entities.user import User
from app.domain.interfaces.user_repository import IUserRepository


class AuthServiceError(Exception):
    """Base exception for auth service errors."""


class EmailAlreadyExistsError(AuthServiceError):
    """Raised when registering with an email that already exists."""


class UsernameAlreadyExistsError(AuthServiceError):
    """Raised when registering with a username that already exists."""


class InvalidCredentialsError(AuthServiceError):
    """Raised when login credentials are wrong."""


class AuthService:
    """Handles user registration and authentication."""

    def __init__(self, user_repo: IUserRepository) -> None:
        self._user_repo = user_repo

    async def register(
        self,
        email: str,
        username: str,
        password: str,
    ) -> tuple[User, str]:
        """
        Register a new user.

        Returns:
            Tuple of (created_user, access_token).

        Raises:
            EmailAlreadyExistsError: If the email is taken.
            UsernameAlreadyExistsError: If the username is taken.
        """
        # Check uniqueness
        if await self._user_repo.get_by_email(email):
            raise EmailAlreadyExistsError(f"Email '{email}' is already registered.")

        if await self._user_repo.get_by_username(username):
            raise UsernameAlreadyExistsError(f"Username '{username}' is already taken.")

        # Create user
        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
        )
        created = await self._user_repo.create(user)

        # Issue token
        token = create_access_token(created.id)
        return created, token

    async def login(self, email: str, password: str) -> tuple[User, str]:
        """
        Authenticate a user by email + password.

        Returns:
            Tuple of (user, access_token).

        Raises:
            InvalidCredentialsError: If email not found or password wrong.
        """
        user = await self._user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password.")

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password.")

        if not user.is_active:
            raise InvalidCredentialsError("Account is deactivated.")

        token = create_access_token(user.id)
        return user, token

    async def get_user(self, user_id: UUID) -> User | None:
        """Retrieve a user by ID (for profile endpoints)."""
        return await self._user_repo.get_by_id(user_id)

"""
Abstract interface for the User repository.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.user import User


class IUserRepository(ABC):
    """Contract for user persistence operations."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Persist a new user and return it with generated fields."""
        ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Find a user by ID, or None if not found."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Find a user by email, or None if not found."""
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Find a user by username, or None if not found."""
        ...

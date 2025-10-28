from __future__ import annotations

from passlib.context import CryptContext


class PasswordHasher:
    """Wrapper around passlib's CryptContext for hashing user passwords."""

    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        """Return a secure hash for ``password``."""

        return self._context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Return True if ``plain_password`` matches ``hashed_password``."""

        try:
            return self._context.verify(plain_password, hashed_password)
        except ValueError:
            return False


__all__ = ["PasswordHasher"]

from typing import Any

from database.repositories.user_limitation_repository import (
    UserLimitationRepository,
)


class UserLimitationService:
    """
    Application-level service for managing a user's
    physical limitations.
    """

    def __init__(self):
        self.repository = UserLimitationRepository()

    def get_limitations(
        self,
        user_id: str,
    ) -> list[str]:
        """
        Return all limitation names for a user.
        """

        return self.repository.get_limitation_names(user_id)

    def set_limitations(
        self,
        user_id: str,
        limitations: list[str],
    ) -> list[dict[str, Any]]:
        """
        Replace the user's complete limitation list.

        Example:
            Existing:
                ["knee"]

            New:
                ["shoulder", "back"]

        Result:
            ["shoulder", "back"]

        An empty list means the user has no reported limitations.
        """

        if not isinstance(limitations, list):
            raise TypeError("limitations must be a list.")

        # Remove old limitations first.
        self.repository.remove_all(user_id)

        # Empty list means no limitations.
        if not limitations:
            return []

        return self.repository.add_many(
            user_id=user_id,
            limitations=limitations,
        )

    def add_limitation(
        self,
        user_id: str,
        limitation: str,
    ) -> dict[str, Any]:
        """
        Add one limitation without removing existing ones.
        """

        return self.repository.add(
            user_id=user_id,
            limitation=limitation,
        )

    def remove_limitation(
        self,
        user_id: str,
        limitation: str,
    ) -> None:
        """
        Remove one limitation.
        """

        self.repository.remove(
            user_id=user_id,
            limitation=limitation,
        )
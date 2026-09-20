from typing import Any

from database.client import get_supabase_client


class UserLimitationRepository:
    """
    Handles database operations for a user's reported
    physical limitations.
    """

    VALID_LIMITATIONS = {
        "knee",
        "hip",
        "shoulder",
        "wrist",
        "back",
        "ankle",
    }

    def __init__(self):
        self.supabase = get_supabase_client()

    def get_by_user_id(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:
        """
        Return all limitations reported by a user.
        """

        self._validate_user_id(user_id)

        response = (
            self.supabase
            .table("user_limitations")
            .select("*")
            .eq("user_id", user_id)
            .order("limitation")
            .execute()
        )

        return response.data or []

    def get_limitation_names(
        self,
        user_id: str,
    ) -> list[str]:
        """
        Return only the limitation names.
        """

        rows = self.get_by_user_id(user_id)

        return [
            row["limitation"]
            for row in rows
            if row.get("limitation")
        ]

    def add(
        self,
        user_id: str,
        limitation: str,
    ) -> dict[str, Any]:
        """
        Add one limitation for a user.
        """

        self._validate_user_id(user_id)

        limitation = self._normalize_limitation(limitation)

        response = (
            self.supabase
            .table("user_limitations")
            .upsert(
                {
                    "user_id": user_id,
                    "limitation": limitation,
                },
                on_conflict="user_id,limitation",
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "User limitation could not be saved."
            )

        return response.data[0]

    def add_many(
        self,
        user_id: str,
        limitations: list[str],
    ) -> list[dict[str, Any]]:
        """
        Add multiple limitations for a user.
        """

        self._validate_user_id(user_id)

        cleaned = self._normalize_many(limitations)

        if not cleaned:
            return []

        records = [
            {
                "user_id": user_id,
                "limitation": limitation,
            }
            for limitation in cleaned
        ]

        response = (
            self.supabase
            .table("user_limitations")
            .upsert(
                records,
                on_conflict="user_id,limitation",
            )
            .execute()
        )

        return response.data or []

    def remove(
        self,
        user_id: str,
        limitation: str,
    ) -> None:
        """
        Remove one limitation from a user's profile.
        """

        self._validate_user_id(user_id)

        limitation = self._normalize_limitation(limitation)

        self.supabase \
            .table("user_limitations") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("limitation", limitation) \
            .execute()

    def remove_all(
        self,
        user_id: str,
    ) -> None:
        """
        Remove all limitations for a user.

        This is useful when the user edits their onboarding
        information and changes the complete limitation list.
        """

        self._validate_user_id(user_id)

        self.supabase \
            .table("user_limitations") \
            .delete() \
            .eq("user_id", user_id) \
            .execute()

    @classmethod
    def _normalize_limitation(
        cls,
        limitation: str,
    ) -> str:
        if not limitation or not limitation.strip():
            raise ValueError(
                "limitation cannot be empty."
            )

        limitation = limitation.strip().lower()

        if limitation not in cls.VALID_LIMITATIONS:
            raise ValueError(
                f"Invalid limitation: {limitation}. "
                f"Allowed values: "
                f"{sorted(cls.VALID_LIMITATIONS)}"
            )

        return limitation

    @classmethod
    def _normalize_many(
        cls,
        limitations: list[str],
    ) -> list[str]:
        if not isinstance(limitations, list):
            raise TypeError(
                "limitations must be a list."
            )

        cleaned = {
            cls._normalize_limitation(limitation)
            for limitation in limitations
        }

        return sorted(cleaned)

    @staticmethod
    def _validate_user_id(user_id: str) -> None:
        if not user_id or not user_id.strip():
            raise ValueError(
                "user_id cannot be empty."
            )
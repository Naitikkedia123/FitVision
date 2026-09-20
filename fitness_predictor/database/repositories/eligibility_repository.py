from typing import Any

from database.client import get_supabase_client


class EligibilityRepository:
    """
    Database access layer for determining exercise eligibility.

    This repository only retrieves exercise and exclusion data.
    It does not make medical decisions by itself.
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    def get_active_exercises(self) -> list[dict[str, Any]]:
        """
        Return all currently active exercises.
        """

        response = (
            self.supabase
            .table("exercises")
            .select("*")
            .eq("active", True)
            .order("difficulty")
            .execute()
        )

        return response.data or []

    def get_excluded_exercise_ids(
        self,
        limitations: list[str],
    ) -> set[str]:
        """
        Return exercise IDs that have an exclusion rule matching
        any of the supplied limitations.

        Example:
            ["knee", "shoulder"]

        returns the set of exercise IDs excluded by either
        limitation.
        """

        if not limitations:
            return set()

        cleaned_limitations = sorted(
            {
                limitation.strip().lower()
                for limitation in limitations
                if limitation and limitation.strip()
            }
        )

        if not cleaned_limitations:
            return set()

        response = (
            self.supabase
            .table("exercise_exclusions")
            .select("exercise_id")
            .in_("limitation", cleaned_limitations)
            .execute()
        )

        rows = response.data or []

        return {
            row["exercise_id"]
            for row in rows
            if row.get("exercise_id")
        }

    def get_eligible_exercises(
        self,
        limitations: list[str],
    ) -> list[dict[str, Any]]:
        """
        Return active exercises after applying the currently
        stored limitation exclusions.
        """

        exercises = self.get_active_exercises()

        excluded_ids = self.get_excluded_exercise_ids(
            limitations
        )

        return [
            exercise
            for exercise in exercises
            if exercise["id"] not in excluded_ids
        ]
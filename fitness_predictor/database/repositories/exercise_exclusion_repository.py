from typing import Any

from database.client import get_supabase_client


class ExerciseExclusionRepository:
    """
    Handles database operations for exercise limitations/exclusions.

    This repository only reads/writes the database relationship.
    It does NOT decide whether a limitation is medically appropriate
    for a particular exercise.
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    def get_excluded_exercises(
        self,
        limitations: list[str],
    ) -> list[str]:
        """
        Return exercise IDs that are excluded for any of the
        supplied user limitations.

        Example:
            ["knee", "shoulder"]
            -> ["squat", "reverse_lunge", ...]
        """

        if not limitations:
            return []

        cleaned_limitations = {
            limitation.strip().lower()
            for limitation in limitations
            if limitation and limitation.strip()
        }

        if not cleaned_limitations:
            return []

        response = (
            self.supabase
            .table("exercise_exclusions")
            .select("exercise_id, limitation")
            .in_("limitation", list(cleaned_limitations))
            .execute()
        )

        rows = response.data or []

        return sorted({
            row["exercise_id"]
            for row in rows
            if row.get("exercise_id")
        })

    def get_exclusions_for_exercise(
        self,
        exercise_id: str,
    ) -> list[dict[str, Any]]:
        """
        Return all limitation exclusions associated with
        one exercise.
        """

        if not exercise_id or not exercise_id.strip():
            raise ValueError("exercise_id cannot be empty.")

        response = (
            self.supabase
            .table("exercise_exclusions")
            .select("*")
            .eq("exercise_id", exercise_id)
            .execute()
        )

        return response.data or []

    def add_exclusion(
        self,
        exercise_id: str,
        limitation: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Add one exercise/limitation exclusion.

        The actual safety decision must be made before calling
        this method.
        """

        if not exercise_id or not exercise_id.strip():
            raise ValueError("exercise_id cannot be empty.")

        if not limitation or not limitation.strip():
            raise ValueError("limitation cannot be empty.")

        record = {
            "exercise_id": exercise_id.strip(),
            "limitation": limitation.strip().lower(),
            "reason": reason,
        }

        response = (
            self.supabase
            .table("exercise_exclusions")
            .upsert(
                record,
                on_conflict="exercise_id,limitation",
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Exercise exclusion was not created."
            )

        return response.data[0]

    def remove_exclusion(
        self,
        exercise_id: str,
        limitation: str,
    ) -> None:
        """
        Remove one exercise/limitation exclusion.
        """

        if not exercise_id or not exercise_id.strip():
            raise ValueError("exercise_id cannot be empty.")

        if not limitation or not limitation.strip():
            raise ValueError("limitation cannot be empty.")

        self.supabase \
            .table("exercise_exclusions") \
            .delete() \
            .eq("exercise_id", exercise_id.strip()) \
            .eq("limitation", limitation.strip().lower()) \
            .execute()
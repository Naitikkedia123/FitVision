from typing import Any

from database.client import get_supabase_client


class ExerciseRepository:
    """
    Handles all database operations related to exercises.

    The rest of the application should use this repository
    instead of writing Supabase queries directly.
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    def get_all(self, active_only: bool = True) -> list[dict[str, Any]]:
        """
        Return all exercises.

        Args:
            active_only: If True, return only active exercises.

        Returns:
            List of exercise records.
        """
        query = self.supabase.table("exercises").select("*")

        if active_only:
            query = query.eq("active", True)

        response = query.order("name").execute()

        return response.data or []

    def get_by_id(self, exercise_id: str) -> dict[str, Any] | None:
        """
        Return one exercise by its ID.
        """
        response = (
            self.supabase
            .table("exercises")
            .select("*")
            .eq("id", exercise_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def get_by_category(
        self,
        category: str,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Return exercises belonging to a category.
        """
        query = (
            self.supabase
            .table("exercises")
            .select("*")
            .eq("category", category)
        )

        if active_only:
            query = query.eq("active", True)

        response = query.order("difficulty").execute()

        return response.data or []

    def get_by_difficulty(
        self,
        min_difficulty: int,
        max_difficulty: int,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Return exercises inside a difficulty range.
        """
        if min_difficulty > max_difficulty:
            raise ValueError(
                "min_difficulty cannot be greater than max_difficulty."
            )

        if not 1 <= min_difficulty <= 5:
            raise ValueError(
                "min_difficulty must be between 1 and 5."
            )

        if not 1 <= max_difficulty <= 5:
            raise ValueError(
                "max_difficulty must be between 1 and 5."
            )

        query = (
            self.supabase
            .table("exercises")
            .select("*")
            .gte("difficulty", min_difficulty)
            .lte("difficulty", max_difficulty)
        )

        if active_only:
            query = query.eq("active", True)

        response = query.order("difficulty").execute()

        return response.data or []

    def insert(self, exercise: dict[str, Any]) -> dict[str, Any]:
        """
        Insert one exercise.
        """
        required_fields = [
            "id",
            "name",
            "category",
            "difficulty",
            "measurement_type",
            "progression_group",
        ]

        missing = [
            field
            for field in required_fields
            if field not in exercise
        ]

        if missing:
            raise ValueError(
                f"Missing required exercise fields: {missing}"
            )

        response = (
            self.supabase
            .table("exercises")
            .insert(exercise)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Exercise insert succeeded but no data was returned."
            )

        return response.data[0]

    def insert_many(
        self,
        exercises: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Insert multiple exercises.
        """
        if not exercises:
            raise ValueError("Exercise list cannot be empty.")

        for index, exercise in enumerate(exercises):
            missing = [
                field
                for field in [
                    "id",
                    "name",
                    "category",
                    "difficulty",
                    "measurement_type",
                    "progression_group",
                ]
                if field not in exercise
            ]

            if missing:
                raise ValueError(
                    f"Exercise at index {index} is missing: {missing}"
                )

        response = (
            self.supabase
            .table("exercises")
            .insert(exercises)
            .execute()
        )

        return response.data or []

    def delete(self, exercise_id: str) -> None:
        """
        Permanently delete an exercise.

        We will rarely use this because the application normally
        prefers setting active=False instead.
        """
        self.supabase \
            .table("exercises") \
            .delete() \
            .eq("id", exercise_id) \
            .execute()

    def deactivate(self, exercise_id: str) -> None:
        """
        Soft-delete an exercise by marking it inactive.
        """
        response = (
            self.supabase
            .table("exercises")
            .update({"active": False})
            .eq("id", exercise_id)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                f"Exercise '{exercise_id}' was not found."
            )
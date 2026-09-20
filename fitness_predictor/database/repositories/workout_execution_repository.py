from typing import Any

from database.client import get_supabase_client


class WorkoutExecutionRepository:
    def __init__(self):
        self.client = get_supabase_client()

    def update_completed_sets(
        self,
        workout_exercise_id: int,
        completed_sets: int,
    ) -> dict[str, Any]:
        if workout_exercise_id <= 0:
            raise ValueError(
                "workout_exercise_id must be greater than 0."
            )

        if completed_sets < 0:
            raise ValueError(
                "completed_sets cannot be negative."
            )

        existing_response = (
            self.client
            .table("workout_exercises")
            .select("sets, completed_sets, status")
            .eq("id", workout_exercise_id)
            .limit(1)
            .execute()
        )

        if not existing_response.data:
            raise RuntimeError(
                "Workout exercise was not found."
            )

        exercise = existing_response.data[0]
        target_sets = exercise["sets"]

        if completed_sets > target_sets:
            raise ValueError(
                "completed_sets cannot exceed target sets."
            )

        status = (
            "completed"
            if completed_sets == target_sets
            else "in_progress"
        )

        response = (
            self.client
            .table("workout_exercises")
            .update(
                {
                    "completed_sets": completed_sets,
                    "status": status,
                }
            )
            .eq("id", workout_exercise_id)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to update workout exercise progress."
            )

        return response.data[0]

    def mark_exercise_completed(
        self,
        workout_exercise_id: int,
    ) -> dict[str, Any]:
        if workout_exercise_id <= 0:
            raise ValueError(
                "workout_exercise_id must be greater than 0."
            )

        response = (
            self.client
            .table("workout_exercises")
            .update(
                {
                    "status": "completed",
                }
            )
            .eq("id", workout_exercise_id)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to mark workout exercise completed."
            )

        return response.data[0]
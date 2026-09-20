from typing import Any

from database.client import get_supabase_client


class WorkoutPlanRepository:
    def __init__(self):
        self.client = get_supabase_client()

    # =========================================================
    # CREATE
    # =========================================================

    def create_plan(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
        total_days: int,
        status: str = "active",
    ) -> dict[str, Any]:
        if not user_id:
            raise ValueError("user_id is required.")

        if not start_date:
            raise ValueError("start_date is required.")

        if not end_date:
            raise ValueError("end_date is required.")

        if total_days <= 0:
            raise ValueError(
                "total_days must be greater than 0."
            )

        if not status:
            raise ValueError("status is required.")

        response = (
            self.client
            .table("workout_plans")
            .insert(
                {
                    "user_id": user_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_days": total_days,
                    "status": status,
                }
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to create workout plan."
            )

        return response.data[0]

    def create_day(
        self,
        plan_id: str,
        day_number: int,
        week_number: int,
        workout_date: str,
        status: str = "available",
    ) -> dict[str, Any]:
        if not plan_id:
            raise ValueError("plan_id is required.")

        if day_number <= 0:
            raise ValueError(
                "day_number must be greater than 0."
            )

        if week_number <= 0:
            raise ValueError(
                "week_number must be greater than 0."
            )

        if not workout_date:
            raise ValueError(
                "workout_date is required."
            )

        if not status:
            raise ValueError("status is required.")

        response = (
            self.client
            .table("workout_days")
            .insert(
                {
                    "plan_id": plan_id,
                    "day_number": day_number,
                    "week_number": week_number,
                    "workout_date": workout_date,
                    "status": status,
                }
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to create workout day."
            )

        return response.data[0]

    def create_exercise(
        self,
        workout_day_id: str,
        exercise_id: str,
        order_index: int,
        sets: int,
        target_reps: int | None,
        target_duration_seconds: int | None,
        status: str = "pending",
    ) -> dict[str, Any]:
        if not workout_day_id:
            raise ValueError(
                "workout_day_id is required."
            )

        if not exercise_id:
            raise ValueError(
                "exercise_id is required."
            )

        if order_index < 1:
            raise ValueError(
                "order_index must be >= 1."
            )

        if sets <= 0:
            raise ValueError(
                "sets must be greater than 0."
            )

        if (
            target_reps is None
            and target_duration_seconds is None
        ):
            raise ValueError(
                "Exactly one of target_reps or "
                "target_duration_seconds is required."
            )

        if (
            target_reps is not None
            and target_duration_seconds is not None
        ):
            raise ValueError(
                "target_reps and target_duration_seconds "
                "cannot both be set."
            )

        if target_reps is not None and target_reps <= 0:
            raise ValueError(
                "target_reps must be greater than 0."
            )

        if (
            target_duration_seconds is not None
            and target_duration_seconds <= 0
        ):
            raise ValueError(
                "target_duration_seconds must be "
                "greater than 0."
            )

        if not status:
            raise ValueError(
                "status is required."
            )

        response = (
            self.client
            .table("workout_exercises")
            .insert(
                {
                    "workout_day_id": workout_day_id,
                    "exercise_id": exercise_id,
                    "order_index": order_index,
                    "sets": sets,
                    "target_reps": target_reps,
                    "target_duration_seconds": (
                        target_duration_seconds
                    ),
                    "status": status,
                }
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to create workout exercise."
            )

        return response.data[0]

    # =========================================================
    # EXECUTION / PROGRESS
    # =========================================================

    def mark_day_started(
        self,
        workout_day_id: str,
    ) -> dict[str, Any]:
        """
        Mark a workout day as in progress.

        This is called when the user actually starts executing
        an exercise from the day.
        """

        if not workout_day_id:
            raise ValueError(
                "workout_day_id is required."
            )

        from datetime import datetime, timezone

        response = (
            self.client
            .table("workout_days")
            .update(
                {
                    "status": "in_progress",
                    "started_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )
            .eq("id", workout_day_id)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to mark workout day as started."
            )

        return response.data[0]

    def update_exercise_progress(
        self,
        workout_exercise_id: str,
        completed_sets: int,
    ) -> dict[str, Any]:
        """
        Persist the number of completed sets for an exercise.

        The exercise remains in_progress until all configured
        sets have been completed.
        """

        if not workout_exercise_id:
            raise ValueError(
                "workout_exercise_id is required."
            )

        if completed_sets < 0:
            raise ValueError(
                "completed_sets cannot be negative."
            )

        exercise_response = (
            self.client
            .table("workout_exercises")
            .select(
                "id, sets, status"
            )
            .eq(
                "id",
                workout_exercise_id,
            )
            .limit(1)
            .execute()
        )

        if not exercise_response.data:
            raise RuntimeError(
                "Workout exercise not found."
            )

        exercise = exercise_response.data[0]

        required_sets = exercise.get("sets")

        if required_sets is None:
            raise RuntimeError(
                "Workout exercise has no required set count."
            )

        if completed_sets > required_sets:
            raise ValueError(
                "completed_sets cannot exceed "
                "the required number of sets."
            )

        status = (
            "completed"
            if completed_sets == required_sets
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
            .eq(
                "id",
                workout_exercise_id,
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to update workout exercise progress."
            )

        return response.data[0]

    def mark_exercise_completed(
        self,
        workout_exercise_id: str,
    ) -> dict[str, Any]:
        """
        Mark an exercise completed.

        Completion is allowed only after all configured
        sets have been completed.
        """

        if not workout_exercise_id:
            raise ValueError(
                "workout_exercise_id is required."
            )

        exercise_response = (
            self.client
            .table("workout_exercises")
            .select(
                "id, sets, completed_sets, status"
            )
            .eq(
                "id",
                workout_exercise_id,
            )
            .limit(1)
            .execute()
        )

        if not exercise_response.data:
            raise RuntimeError(
                "Workout exercise not found."
            )

        exercise = exercise_response.data[0]

        required_sets = exercise.get("sets")

        if required_sets is None:
            raise RuntimeError(
                "Workout exercise has no required set count."
            )

        completed_sets = (
            exercise.get("completed_sets") or 0
        )

        if completed_sets < required_sets:
            raise ValueError(
                "Cannot mark exercise completed before "
                "all sets are completed."
            )

        response = (
            self.client
            .table("workout_exercises")
            .update(
                {
                    "completed_sets": required_sets,
                    "status": "completed",
                }
            )
            .eq(
                "id",
                workout_exercise_id,
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to mark workout exercise as completed."
            )

        return response.data[0]

    def get_next_exercise(
        self,
        workout_day_id: str,
        current_order_index: int,
    ) -> dict[str, Any] | None:
        """
        Return the next unfinished exercise in execution order.
        """

        if not workout_day_id:
            raise ValueError(
                "workout_day_id is required."
            )

        if current_order_index < 1:
            raise ValueError(
                "current_order_index must be >= 1."
            )

        response = (
            self.client
            .table("workout_exercises")
            .select("*")
            .eq(
                "workout_day_id",
                workout_day_id,
            )
            .gt(
                "order_index",
                current_order_index,
            )
            .neq(
                "status",
                "completed",
            )
            .order(
                "order_index",
                desc=False,
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def mark_day_completed(
        self,
        workout_day_id: str,
    ) -> dict[str, Any]:
        """
        Mark a workout day completed only when every exercise
        belonging to that day is completed.
        """

        if not workout_day_id:
            raise ValueError(
                "workout_day_id is required."
            )

        exercises_response = (
            self.client
            .table("workout_exercises")
            .select(
                "id, status"
            )
            .eq(
                "workout_day_id",
                workout_day_id,
            )
            .execute()
        )

        exercises = exercises_response.data or []

        if not exercises:
            raise ValueError(
                "Cannot complete a workout day with no exercises."
            )

        if any(
            exercise.get("status") != "completed"
            for exercise in exercises
        ):
            raise ValueError(
                "Cannot mark workout day completed while "
                "exercises remain unfinished."
            )

        from datetime import datetime, timezone

        response = (
            self.client
            .table("workout_days")
            .update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )
            .eq(
                "id",
                workout_day_id,
            )
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to mark workout day as completed."
            )

        return response.data[0]   

    def get_plan_exercises(
        self,
        workout_day_ids: list[str],
    ) -> list[dict[str, Any]]:
        """
        Return all exercises belonging to the supplied workout days
        in a single database request.

        This avoids one Supabase request per day when loading the
        28-day dashboard.
        """

        if not workout_day_ids:
            return []

        normalized_ids = [
            str(day_id)
            for day_id in workout_day_ids
            if day_id
        ]

        if not normalized_ids:
            return []

        response = (
            self.client
            .table("workout_exercises")
            .select("*")
            .in_(
                "workout_day_id",
                normalized_ids,
            )
            .order(
                "workout_day_id",
                desc=False,
            )
            .order(
                "order_index",
                desc=False,
            )
            .execute()
        )

        return response.data or []

    # =========================================================
    # READ
    # =========================================================

    def get_active_plan(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """
        Return the user's most recently created active plan.

        Returns None when the user does not currently have
        an active plan.
        """

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        response = (
            self.client
            .table("workout_plans")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "active")
            .order(
                "created_at",
                desc=True,
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    def get_plan_days(
        self,
        plan_id: str,
    ) -> list[dict[str, Any]]:
        """
        Return all workout days belonging to a plan,
        ordered by their sequence in the 28-day program.
        """

        if not plan_id:
            raise ValueError(
                "plan_id is required."
            )

        response = (
            self.client
            .table("workout_days")
            .select("*")
            .eq("plan_id", plan_id)
            .order(
                "day_number",
                desc=False,
            )
            .execute()
        )

        return response.data or []

    def get_day_exercises(
        self,
        workout_day_id: str,
    ) -> list[dict[str, Any]]:
        """
        Return all exercises belonging to a workout day,
        ordered by execution order.
        """

        if not workout_day_id:
            raise ValueError(
                "workout_day_id is required."
            )

        response = (
            self.client
            .table("workout_exercises")
            .select("*")
            .eq(
                "workout_day_id",
                workout_day_id,
            )
            .order(
                "order_index",
                desc=False,
            )
            .execute()
        )

        return response.data or []
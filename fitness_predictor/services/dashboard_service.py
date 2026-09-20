from datetime import date
from typing import Any

from database.repositories.workout_plan_repository import (
    WorkoutPlanRepository,
)
from services.workout_state_service import WorkoutStateService


class DashboardService:
    """
    Read-only service for the user's active workout plan.

    Dashboard reads are batched so a 28-day plan does not cause one
    database request per workout day.
    """

    def __init__(self, repository=None):
        self.repository = repository or WorkoutPlanRepository()
        self.state_service = WorkoutStateService()

    def get_active_plan(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        plan = self.repository.get_active_plan(
            user_id
        )

        if plan is None:
            return None

        days = self.repository.get_plan_days(
            plan_id=str(plan["id"])
        )

        day_ids = [
            str(day["id"])
            for day in days
            if day.get("id") is not None
        ]

        exercises = self.repository.get_plan_exercises(
            workout_day_ids=day_ids
        )

        exercises_by_day: dict[str, list[dict[str, Any]]] = {
            day_id: []
            for day_id in day_ids
        }

        for exercise in exercises:
            day_id = exercise.get("workout_day_id")

            if day_id is None:
                continue

            exercises_by_day.setdefault(
                str(day_id),
                [],
            ).append(exercise)

        for day in days:
            day["exercises"] = exercises_by_day.get(
                str(day["id"]),
                [],
            )

        plan_with_days = {
            **plan,
            "days": days,
        }

        return self.state_service.decorate_plan(
            plan_with_days,
            today=date.today(),
        )

    def get_current_day(
        self,
        user_id: str | None = None,
        *,
        plan: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Return the currently available workout day.

        Pass an already-loaded `plan` from the dashboard to avoid
        fetching the entire plan a second time.
        """

        if plan is None:
            if not user_id:
                raise ValueError(
                    "user_id is required when plan is not provided."
                )

            plan = self.get_active_plan(
                user_id
            )

        if plan is None:
            return None

        for day in plan.get("days", []):
            if (
                day.get("workout_state")
                == self.state_service.AVAILABLE
            ):
                return day

        return None

from __future__ import annotations

from datetime import date
from typing import Any


class WorkoutStateService:
    """
    Determines the state of each workout day.

    States:
        - completed
        - available
        - locked
        - missed

    Rules:

        1. Completed days remain completed.
        2. Today's day is available.
        3. Future days are locked.
        4. Past incomplete days become missed.
        5. The 28-day calendar does not shift when a day is missed.

    This service is UI-independent.
    """

    COMPLETED = "completed"
    AVAILABLE = "available"
    LOCKED = "locked"
    MISSED = "missed"

    def get_day_state(
        self,
        day: dict[str, Any],
        *,
        today: date,
        previous_day_completed: bool = True,
    ) -> str:
        """
        Determine the state of one workout day.

        `previous_day_completed` is currently accepted for
        compatibility with the plan decoration flow, but today's
        availability is determined by calendar date, not by the
        previous day's completion.

        This means:
            Past incomplete -> missed
            Today -> available
            Future -> locked
        """

        status = str(
            day.get("status") or ""
        ).strip().lower()

        # A completed workout day always stays completed.
        if status == self.COMPLETED:
            return self.COMPLETED

        workout_date = self._parse_workout_date(
            day.get("workout_date")
        )

        # Invalid/missing dates must never accidentally become
        # executable.
        if workout_date is None:
            return self.LOCKED

        # Future calendar days cannot be opened early.
        if workout_date > today:
            return self.LOCKED

        # Today's workout is available regardless of whether
        # the previous calendar day was completed.
        if workout_date == today:
            return self.AVAILABLE

        # Any incomplete day whose date has already passed is
        # considered missed.
        return self.MISSED

    def decorate_plan(
        self,
        plan: dict[str, Any],
        *,
        today: date | None = None,
    ) -> dict[str, Any]:
        """
        Add deterministic state information to every workout day.

        The original plan object is not mutated.
        """

        resolved_today = today or date.today()

        days = plan.get("days", [])

        decorated_days: list[dict[str, Any]] = []

        for day in days:
            day_copy = dict(day)

            exercises = day_copy.get(
                "exercises",
                [],
            )

            exercise_list = [
                dict(exercise)
                for exercise in exercises
            ]

            day_copy["exercises"] = exercise_list

            day_completed = self.is_day_completed(
                exercise_list
            )

            day_copy["is_completed"] = day_completed

            # Derive the state from the calendar date and
            # actual completion status.
            if day_completed:
                day_copy["workout_state"] = self.COMPLETED
            else:
                day_copy["workout_state"] = self.get_day_state(
                    day_copy,
                    today=resolved_today,
                )

            decorated_days.append(day_copy)

        return {
            **plan,
            "days": decorated_days,
            "today": resolved_today.isoformat(),
        }

    @staticmethod
    def is_day_completed(
        exercises: list[dict[str, Any]],
    ) -> bool:
        """
        A workout day is completed only when every planned
        exercise has completed status.
        """

        if not exercises:
            return False

        return all(
            str(
                exercise.get("status") or ""
            ).strip().lower()
            == "completed"
            for exercise in exercises
        )

    @staticmethod
    def get_current_day(
        plan: dict[str, Any],
        *,
        today: date | None = None,
    ) -> dict[str, Any] | None:
        """
        Return the workout day whose workout_date matches today.
        """

        resolved_today = today or date.today()

        for day in plan.get("days", []):
            workout_date = WorkoutStateService._parse_workout_date(
                day.get("workout_date")
            )

            if workout_date == resolved_today:
                return day

        return None

    @staticmethod
    def get_first_incomplete_day(
        plan: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Return the first day that has not been completed.

        This is kept as a utility for later compatibility.
        """

        for day in plan.get("days", []):
            if not day.get(
                "is_completed",
                False,
            ):
                return day

        return None

    @staticmethod
    def _parse_workout_date(
        value: Any,
    ) -> date | None:
        """
        Safely convert a Supabase date/datetime/string value
        into a Python date.
        """

        if value is None:
            return None

        if isinstance(value, date):
            return value

        try:
            return date.fromisoformat(
                str(value)[:10]
            )
        except (TypeError, ValueError):
            return None
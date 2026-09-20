from datetime import date, timedelta
from typing import Any

from database.repositories.workout_plan_repository import (
    WorkoutPlanRepository,
)
from models.user_profile import UserProfile


class PlanPersistenceService:
    def __init__(self, repository=None):
        self.repository = repository or WorkoutPlanRepository()

    def save_plan(
        self,
        user: UserProfile,
        four_week_plan: dict[
            int,
            dict[int, list[dict[str, Any]]]
        ],
        start_date: date,
    ) -> dict[str, Any]:
        """
        Persist the current four-week daily workout plan.

        Expected structure:

            {
                1: {
                    1: [exercise, ...],
                    2: [exercise, ...],
                    ...
                    7: [exercise, ...],
                },
                2: {
                    1: [exercise, ...],
                    ...
                },
                3: {...},
                4: {...},
            }

        The outer key is the week number.
        The inner key is the day number within that week.
        """

        if not isinstance(user, UserProfile):
            raise TypeError("user must be a UserProfile.")

        if not isinstance(four_week_plan, dict):
            raise TypeError(
                "four_week_plan must be a dictionary."
            )

        if set(four_week_plan.keys()) != {1, 2, 3, 4}:
            raise ValueError(
                "four_week_plan must contain exactly "
                "weeks 1, 2, 3, and 4."
            )

        if not isinstance(start_date, date):
            raise TypeError(
                "start_date must be a date."
            )

        end_date = start_date + timedelta(days=27)

        plan_row = self.repository.create_plan(
            user_id=user.user_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            total_days=28,
            status="active",
        )

        plan_id = plan_row["id"]

        saved_days = []

        day_offset = 0

        for week_number in range(1, 5):
            week_plan = four_week_plan[week_number]

            if not isinstance(week_plan, dict):
                raise TypeError(
                    f"Week {week_number} must be a dictionary "
                    "of day numbers to exercise lists."
                )

            if set(week_plan.keys()) != {
                1, 2, 3, 4, 5, 6, 7
            }:
                raise ValueError(
                    f"Week {week_number} must contain "
                    "exactly days 1 through 7."
                )

            for day_number in range(1, 8):
                exercises = week_plan[day_number]

                if not isinstance(exercises, list):
                    raise TypeError(
                        f"Week {week_number}, day {day_number} "
                        "must contain a list of exercises."
                    )

                workout_date = (
                    start_date
                    + timedelta(days=day_offset)
                )

                day_row = self.repository.create_day(
                    plan_id=str(plan_id),
                    day_number=day_offset + 1,
                    week_number=week_number,
                    workout_date=workout_date.isoformat(),
                    status="available",
                )

                day_id = day_row["id"]

                saved_exercises = []

                for order_index, exercise in enumerate(
                    exercises,
                    start=1,
                ):
                    exercise_row = (
                        self.repository.create_exercise(
                            workout_day_id=str(day_id),
                            exercise_id=exercise["id"],
                            order_index=order_index,
                            sets=exercise["sets"],
                            target_reps=exercise["reps"],
                            target_duration_seconds=(
                                exercise["duration_seconds"]
                            ),
                            status="pending",
                        )
                    )

                    saved_exercises.append(
                        exercise_row
                    )

                saved_days.append(
                    {
                        **day_row,
                        "exercises": saved_exercises,
                    }
                )

                day_offset += 1

        return {
            **plan_row,
            "days": saved_days,
        }
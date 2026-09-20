from typing import Any

from models.user_profile import UserProfile
from planning.exposure_progression import progress_dosage_by_exposure
from planning.plan_generator import get_max_exercises
from planning.weekly_scheduler import generate_four_week_schedule
from services.week1_dosage_service import Week1DosageService

from integration.workout_adapter import (
    filter_executable_exercises,
)

class FourWeekPlanService:
    def __init__(self, dosage_service=None):
        self.dosage_service = dosage_service or Week1DosageService()

    def generate(
        self,
        user: UserProfile,
        eligible_exercises: list[dict[str, Any]],
    ) -> dict[int, dict[int, list[dict[str, Any]]]]:
        if not isinstance(user, UserProfile):
            raise TypeError("user must be a UserProfile.")

        if not isinstance(eligible_exercises, list):
            raise TypeError("eligible_exercises must be a list.")

        if not eligible_exercises:
            raise ValueError(
                "eligible_exercises cannot be empty."
            )

        executable_exercises = filter_executable_exercises(
            eligible_exercises
        )

        if not executable_exercises:
            raise ValueError(
                "No eligible exercises are currently supported "
                "by the AI GYM execution engine."
            )

        total_exercises = get_max_exercises(
            workout_time_min=user.workout_time_min,
            plan_max_exercises=6,
        )

        schedule = generate_four_week_schedule(
            eligible_exercises=executable_exercises,
            total_exercises=total_exercises,
            activity_level=user.activity_level,
        )

        # Predict and validate Week-1 dosage for every
        # executable exercise.
        all_dosages = self.dosage_service.generate(
            user,
            executable_exercises,
        )

        dosage_by_exercise_id = {
            dosage.exercise_id: dosage
            for dosage in all_dosages
        }

        # Track how many times each exercise has appeared.
        exposure_counts: dict[str, int] = {}

        plan: dict[
            int,
            dict[int, list[dict[str, Any]]]
        ] = {}

        for week_number in range(1, 5):
            plan[week_number] = {}

            for day_number in range(1, 8):
                exercises = schedule[
                    week_number
                ][day_number]

                day_plan = []

                for exercise in exercises:
                    exercise_id = exercise["id"]

                    week1_dosage = dosage_by_exercise_id.get(
                        exercise_id
                    )

                    if week1_dosage is None:
                        raise ValueError(
                            f"Missing Week 1 dosage for exercise "
                            f"{exercise_id!r}."
                        )

                    # This is the next exposure for this exercise.
                    exposure_counts[exercise_id] = (
                        exposure_counts.get(
                            exercise_id,
                            0,
                        )
                        + 1
                    )

                    exposure_number = exposure_counts[
                        exercise_id
                    ]

                    dosage = progress_dosage_by_exposure(
                        week1_dosage,
                        exposure_number,
                    )

                    day_plan.append(
                        {
                            **exercise,
                            "sets": dosage.sets,
                            "reps": dosage.reps,
                            "duration_seconds": (
                                dosage.duration_seconds
                            ),
                            "exposure_number": exposure_number,
                        }
                    )

                if not day_plan:
                    raise RuntimeError(
                        f"Week {week_number}, Day {day_number} "
                        "contains no exercises."
                    )

                plan[week_number][day_number] = day_plan

        return plan
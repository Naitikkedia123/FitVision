from typing import Any

from ml.prediction import (
    DosagePrediction,
    Week1DosagePredictor,
)
from models.user_profile import UserProfile


class BaselineDosagePredictor(
    Week1DosagePredictor
):
    """
    Temporary predictor used until the trained ML model exists.

    This is NOT the final ML model.

    It provides a deterministic baseline so the entire
    application pipeline can be developed and tested.
    """

    def predict(
        self,
        user: UserProfile,
        exercise: dict[str, Any],
    ) -> DosagePrediction:

        if not isinstance(user, UserProfile):
            raise TypeError(
                "user must be a UserProfile."
            )

        if not isinstance(exercise, dict):
            raise TypeError(
                "exercise must be a dictionary."
            )

        exercise_id = exercise.get("id")

        if not exercise_id:
            raise ValueError(
                "Exercise is missing its id."
            )

        measurement_type = exercise.get(
            "measurement_type"
        )

        # -----------------------------------------------------
        # Temporary baseline only.
        # Actual ML will replace this.
        # -----------------------------------------------------

        sets_by_fitness = {
            1: 1,
            2: 2,
            3: 2,
            4: 3,
            5: 3,
        }

        reps_by_fitness = {
            1: 6,
            2: 8,
            3: 10,
            4: 12,
            5: 12,
        }

        duration_by_fitness = {
            1: 15,
            2: 20,
            3: 30,
            4: 30,
            5: 45,
        }

        sets = sets_by_fitness[
            user.fitness_level
        ]

        if measurement_type == "reps":

            return DosagePrediction(
                exercise_id=exercise_id,
                sets=float(sets),
                reps=float(
                    reps_by_fitness[
                        user.fitness_level
                    ]
                ),
            )

        if measurement_type == "time":

            return DosagePrediction(
                exercise_id=exercise_id,
                sets=float(sets),
                duration_seconds=float(
                    duration_by_fitness[
                        user.fitness_level
                    ]
                ),
            )

        raise ValueError(
            f"Unsupported measurement_type: "
            f"{measurement_type!r}"
        )
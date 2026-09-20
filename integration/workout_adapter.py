from dataclasses import dataclass
from typing import Any

from shared.exercise_mapping import (
    get_execution_spec,
    get_trainer_exercise_type,
    is_trainer_supported,
)


@dataclass(frozen=True)
class WorkoutExecutionConfig:
    """
    Represents one persisted workout exercise after it has been
    translated into something the AI GYM execution layer can use.

    This is an integration-layer object.

    The fitness predictor decides WHAT the user should do.
    The AI GYM decides HOW to execute it.
    """

    exercise_id: str
    trainer_exercise_type: str
    order_index: int
    sets: int
    target_reps: int | None
    target_duration_seconds: int | None
    measurement_type: str
    workout_exercise_id: str
    workout_day_id: str


def adapt_workout_exercise(
    workout_exercise: dict[str, Any],
) -> WorkoutExecutionConfig:
    """
    Convert a persisted workout_exercises row into an
    AI GYM execution configuration.

    Expected input:

        {
            "exercise_id": "bodyweight_squat",
            "order_index": 1,
            "sets": 2,
            "target_reps": 12,
            "target_duration_seconds": None,
            ...
        }

    The adapter does not modify the database row.
    """

    if not isinstance(workout_exercise, dict):
        raise TypeError(
            "workout_exercise must be a dictionary."
        )

    exercise_id = workout_exercise.get("exercise_id")

    if not isinstance(exercise_id, str) or not exercise_id.strip():
        raise ValueError(
            "workout_exercise must contain a valid exercise_id."
        )
    

    exercise_id = exercise_id.strip()

    # ---------------------------------------------------------
    # Validate that the exercise exists in the shared contract.
    # ---------------------------------------------------------

    spec = get_execution_spec(exercise_id)

    if not spec.supported:
        raise ValueError(
            f"Exercise '{exercise_id}' is not currently "
            "supported by the AI GYM execution engine."
        )
    workout_exercise_id = workout_exercise.get("id")
    workout_day_id = workout_exercise.get("workout_day_id")

    if workout_exercise_id is None:
        raise ValueError(
            "workout_exercise must contain its database id."
        )

    if workout_day_id is None:
        raise ValueError(
            "workout_exercise must contain workout_day_id."
        )

    workout_exercise_id = str(workout_exercise_id)
    workout_day_id = str(workout_day_id)

    trainer_exercise_type = get_trainer_exercise_type(
        exercise_id
    )

    # ---------------------------------------------------------
    # Read persisted dosage.
    # ---------------------------------------------------------

    order_index = workout_exercise.get("order_index")

    if not isinstance(order_index, int):
        raise TypeError(
            "order_index must be an integer."
        )

    if order_index < 1:
        raise ValueError(
            "order_index must be >= 1."
        )

    sets = workout_exercise.get("sets")

    if not isinstance(sets, int):
        raise TypeError(
            "sets must be an integer."
        )

    if sets <= 0:
        raise ValueError(
            "sets must be greater than 0."
        )

    target_reps = workout_exercise.get(
        "target_reps"
    )

    target_duration_seconds = (
        workout_exercise.get(
            "target_duration_seconds"
        )
    )

    # ---------------------------------------------------------
    # Enforce exactly one measurement target.
    # ---------------------------------------------------------

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

    if target_reps is not None:
        if not isinstance(target_reps, int):
            raise TypeError(
                "target_reps must be an integer."
            )

        if target_reps <= 0:
            raise ValueError(
                "target_reps must be greater than 0."
            )

        measurement_type = "reps"

    else:
        if not isinstance(
            target_duration_seconds,
            int,
        ):
            raise TypeError(
                "target_duration_seconds "
                "must be an integer."
            )

        if target_duration_seconds <= 0:
            raise ValueError(
                "target_duration_seconds "
                "must be greater than 0."
            )

        measurement_type = "time"

    # ---------------------------------------------------------
    # Return execution-ready configuration.
    # ---------------------------------------------------------

    return WorkoutExecutionConfig(
        exercise_id=exercise_id,
        trainer_exercise_type=trainer_exercise_type,
        order_index=order_index,
        sets=sets,
        target_reps=target_reps,
        target_duration_seconds=target_duration_seconds,
        measurement_type=measurement_type,
        workout_exercise_id=workout_exercise_id,
        workout_day_id=workout_day_id,
    )


def is_workout_exercise_executable(
    workout_exercise: dict[str, Any],
) -> bool:
    """
    Return True when a persisted workout exercise can currently
    be executed by the AI GYM trainer.

    This helper is useful while the remaining exercise detectors
    are being implemented.
    """

    if not isinstance(workout_exercise, dict):
        return False

    exercise_id = workout_exercise.get(
        "exercise_id"
    )

    if not isinstance(exercise_id, str):
        return False

    if not is_trainer_supported(exercise_id):
        return False

    try:
        adapt_workout_exercise(
            workout_exercise
        )
    except (TypeError, ValueError):
        return False

    return True

def filter_executable_exercises(
    exercises: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Return only exercises that the current AI GYM execution
    layer supports.

    This is an execution-capability filter, not a safety filter.
    Safety/eligibility decisions must already have happened before
    this function is called.
    """

    if not isinstance(exercises, list):
        raise TypeError("exercises must be a list.")

    executable = []

    for exercise in exercises:
        if not isinstance(exercise, dict):
            raise TypeError(
                "Each exercise must be a dictionary."
            )

        exercise_id = exercise.get("id")

        if not isinstance(exercise_id, str) or not exercise_id.strip():
            raise ValueError(
                "Each exercise must contain a valid id."
            )

        if is_trainer_supported(exercise_id.strip()):
            executable.append(exercise)

    return executable
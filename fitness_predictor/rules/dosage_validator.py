import math
from dataclasses import dataclass

from data.dosage_config import get_dosage_constraints
from ml.prediction import DosagePrediction


@dataclass(frozen=True)
class ValidatedDosage:
    """
    Final dosage after deterministic validation.

    Exactly one of:
        reps
        duration_seconds

    is populated.
    """

    exercise_id: str
    sets: int

    reps: int | None = None
    duration_seconds: int | None = None

    def validate(self) -> None:
        if not self.exercise_id:
            raise ValueError("exercise_id cannot be empty.")

        if self.sets < 1:
            raise ValueError("sets must be at least 1.")

        has_reps = self.reps is not None
        has_duration = self.duration_seconds is not None

        if has_reps == has_duration:
            raise ValueError(
                "Exactly one of reps or duration_seconds "
                "must be provided."
            )

        if self.reps is not None and self.reps < 1:
            raise ValueError("reps must be at least 1.")

        if (
            self.duration_seconds is not None
            and self.duration_seconds < 1
        ):
            raise ValueError(
                "duration_seconds must be at least 1."
            )


def _is_finite_number(value: object) -> bool:
    """
    Return True only for finite int/float values.
    """
    return (
        isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _round_positive(value: float) -> int:
    """
    Convert a continuous ML prediction into a positive integer.
    """
    return max(1, int(round(value)))


def validate_prediction(
    prediction: DosagePrediction,
) -> ValidatedDosage:
    """
    Convert an ML prediction into a validated final dosage.

    This function is the deterministic safety boundary between
    ML and the workout planner.

    ML may predict arbitrary continuous values, but the final
    dosage is always constrained by our exercise-specific
    dosage configuration.
    """

    if not isinstance(
        prediction,
        DosagePrediction,
    ):
        raise TypeError(
            "prediction must be a DosagePrediction."
        )

    prediction.validate_structure()

    # ---------------------------------------------------------
    # Reject invalid ML outputs
    # ---------------------------------------------------------

    if not _is_finite_number(prediction.sets):
        raise ValueError(
            f"Invalid sets prediction for "
            f"{prediction.exercise_id}: "
            f"{prediction.sets!r}"
        )

    if prediction.reps is not None:
        if not _is_finite_number(prediction.reps):
            raise ValueError(
                f"Invalid reps prediction for "
                f"{prediction.exercise_id}: "
                f"{prediction.reps!r}"
            )

    if prediction.duration_seconds is not None:
        if not _is_finite_number(
            prediction.duration_seconds
        ):
            raise ValueError(
                f"Invalid duration prediction for "
                f"{prediction.exercise_id}: "
                f"{prediction.duration_seconds!r}"
            )

    # ---------------------------------------------------------
    # Load exercise-specific limits
    # ---------------------------------------------------------

    constraints = get_dosage_constraints(
        prediction.exercise_id
    )

    # ---------------------------------------------------------
    # Sets
    # ---------------------------------------------------------

    sets = _round_positive(
        float(prediction.sets)
    )

    sets = max(
        constraints.min_sets,
        min(
            sets,
            constraints.max_sets,
        ),
    )

    # ---------------------------------------------------------
    # Reps-based exercise
    # ---------------------------------------------------------

    if prediction.reps is not None:

        if constraints.measurement_type != "reps":
            raise ValueError(
                f"Exercise '{prediction.exercise_id}' is "
                f"not reps-based, but ML predicted reps."
            )

        reps = _round_positive(
            float(prediction.reps)
        )

        reps = max(
            constraints.min_reps,
            min(
                reps,
                constraints.max_reps,
            ),
        )

        result = ValidatedDosage(
            exercise_id=prediction.exercise_id,
            sets=sets,
            reps=reps,
        )

        result.validate()

        return result

    # ---------------------------------------------------------
    # Time-based exercise
    # ---------------------------------------------------------

    if prediction.duration_seconds is not None:

        if constraints.measurement_type != "time":
            raise ValueError(
                f"Exercise '{prediction.exercise_id}' is "
                f"not time-based, but ML predicted duration."
            )

        duration = _round_positive(
            float(prediction.duration_seconds)
        )

        duration = max(
            constraints.min_duration_seconds,
            min(
                duration,
                constraints.max_duration_seconds,
            ),
        )

        result = ValidatedDosage(
            exercise_id=prediction.exercise_id,
            sets=sets,
            duration_seconds=duration,
        )

        result.validate()

        return result

    raise ValueError(
        "Prediction contains neither reps nor duration."
    )


def validate_predictions(
    predictions: list[DosagePrediction],
) -> list[ValidatedDosage]:
    """
    Validate a collection of ML predictions.
    """

    if not isinstance(predictions, list):
        raise TypeError(
            "predictions must be a list."
        )

    validated: list[ValidatedDosage] = []

    for prediction in predictions:
        validated.append(
            validate_prediction(prediction)
        )

    return validated
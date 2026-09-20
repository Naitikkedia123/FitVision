from dataclasses import dataclass
from typing import Literal


MeasurementType = Literal["reps", "time"]


@dataclass(frozen=True)
class DosageConstraints:
    """
    Valid engineering bounds for an exercise's dosage.

    IMPORTANT:
    These are prototype constraints for the ML system.
    They are NOT individualized medical prescriptions.
    """

    measurement_type: MeasurementType

    min_sets: int
    max_sets: int

    min_reps: int | None = None
    max_reps: int | None = None

    min_duration_seconds: int | None = None
    max_duration_seconds: int | None = None

    def validate(self) -> None:
        if not 1 <= self.min_sets <= self.max_sets:
            raise ValueError(
                "Invalid set range."
            )

        if self.measurement_type == "reps":
            if (
                self.min_reps is None
                or self.max_reps is None
            ):
                raise ValueError(
                    "Rep constraints are required "
                    "for reps-based exercises."
                )

            if not (
                1 <= self.min_reps <= self.max_reps
            ):
                raise ValueError(
                    "Invalid rep range."
                )

            if (
                self.min_duration_seconds is not None
                or self.max_duration_seconds is not None
            ):
                raise ValueError(
                    "Time constraints are not allowed "
                    "for reps-based exercises."
                )

        elif self.measurement_type == "time":
            if (
                self.min_duration_seconds is None
                or self.max_duration_seconds is None
            ):
                raise ValueError(
                    "Duration constraints are required "
                    "for time-based exercises."
                )

            if not (
                1
                <= self.min_duration_seconds
                <= self.max_duration_seconds
            ):
                raise ValueError(
                    "Invalid duration range."
                )

            if (
                self.min_reps is not None
                or self.max_reps is not None
            ):
                raise ValueError(
                    "Rep constraints are not allowed "
                    "for time-based exercises."
                )

        else:
            raise ValueError(
                f"Unsupported measurement type: "
                f"{self.measurement_type}"
            )


# ------------------------------------------------------------
# Prototype engineering bounds
# ------------------------------------------------------------
#
# These values define the space in which the ML predictor may
# operate. They are NOT the model's predictions.
#
# We intentionally keep the bounds broad enough for different
# fitness levels and let the model predict the person's dosage
# inside this validated engineering space.
#
# Reps-based exercises:
#   sets: 1–3
#   reps: 6–15
#
# Time-based exercises:
#   sets: 1–3
#   duration: 15–60 seconds
#
# These are prototype bounds and require later professional
# review before being treated as fitness prescriptions.


DEFAULT_REP_CONSTRAINTS = DosageConstraints(
    measurement_type="reps",
    min_sets=1,
    max_sets=3,
    min_reps=6,
    max_reps=15,
)


DEFAULT_TIME_CONSTRAINTS = DosageConstraints(
    measurement_type="time",
    min_sets=1,
    max_sets=3,
    min_duration_seconds=15,
    max_duration_seconds=60,
)


DOSAGE_CONSTRAINTS: dict[str, DosageConstraints] = {
    # Cardio
    "march_in_place": DEFAULT_TIME_CONSTRAINTS,

    "standing_knee_raise": DEFAULT_REP_CONSTRAINTS,

    "low_impact_jumping_jack": DEFAULT_REP_CONSTRAINTS,

    # Lower body
    "bodyweight_squat": DEFAULT_REP_CONSTRAINTS,

    "reverse_lunge": DEFAULT_REP_CONSTRAINTS,

    "wall_sit": DEFAULT_TIME_CONSTRAINTS,

    "standing_side_leg_raise": DEFAULT_REP_CONSTRAINTS,

    "hamstring_curl": DEFAULT_REP_CONSTRAINTS,

    "hip_extension": DEFAULT_REP_CONSTRAINTS,

    "calf_raise": DEFAULT_REP_CONSTRAINTS,

    "glute_bridge": DEFAULT_REP_CONSTRAINTS,

    "sit_to_stand": DEFAULT_REP_CONSTRAINTS,

    # Upper body
    "wall_push_up": DEFAULT_REP_CONSTRAINTS,

    "knee_push_up": DEFAULT_REP_CONSTRAINTS,

    "standard_push_up": DEFAULT_REP_CONSTRAINTS,

    "shoulder_press": DEFAULT_REP_CONSTRAINTS,

    "biceps_curl": DEFAULT_REP_CONSTRAINTS,

    # Core
    "plank": DEFAULT_TIME_CONSTRAINTS,
}


def get_dosage_constraints(
    exercise_id: str,
) -> DosageConstraints:
    """
    Return dosage constraints for an exercise.
    """

    if not exercise_id:
        raise ValueError(
            "exercise_id cannot be empty."
        )

    try:
        constraints = DOSAGE_CONSTRAINTS[
            exercise_id
        ]
    except KeyError as exc:
        raise KeyError(
            f"No dosage constraints defined for "
            f"exercise: {exercise_id}"
        ) from exc

    constraints.validate()

    return constraints


def validate_all_constraints() -> None:
    """
    Validate the complete dosage configuration.
    """

    if len(DOSAGE_CONSTRAINTS) != 18:
        raise ValueError(
            f"Expected dosage constraints for 18 exercises, "
            f"found {len(DOSAGE_CONSTRAINTS)}."
        )

    for exercise_id, constraints in DOSAGE_CONSTRAINTS.items():
        try:
            constraints.validate()
        except ValueError as exc:
            raise ValueError(
                f"Invalid constraints for "
                f"{exercise_id}: {exc}"
            ) from exc
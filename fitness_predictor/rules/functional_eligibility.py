from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FunctionalRestrictions:
    """
    Explicit functional restrictions for a user.

    These are not medical diagnoses.

    They represent movement/activity restrictions that have
    actually been established for the user.
    """

    max_impact_level: int | None = None
    max_knee_flexion_level: int | None = None
    max_hip_load_level: int | None = None
    max_back_load_level: int | None = None
    max_ankle_load_level: int | None = None

    avoid_overhead_shoulder: bool = False
    avoid_wrist_weight_bearing: bool = False
    avoid_floor_exercises: bool = False
    avoid_single_leg: bool = False

    def validate(self) -> None:
        """
        Validate restriction values.
        """

        for field_name in (
            "max_impact_level",
            "max_knee_flexion_level",
            "max_hip_load_level",
            "max_back_load_level",
            "max_ankle_load_level",
        ):
            value = getattr(self, field_name)

            if value is not None and not 0 <= value <= 3:
                raise ValueError(
                    f"{field_name} must be between 0 and 3."
                )


@dataclass(frozen=True)
class EligibilityDecision:
    """
    Result of checking one exercise against functional restrictions.
    """

    eligible: bool
    reasons: tuple[str, ...] = ()


def evaluate_exercise(
    exercise: dict[str, Any],
    restrictions: FunctionalRestrictions,
) -> EligibilityDecision:
    """
    Determine whether an exercise satisfies the supplied
    functional restrictions.

    This function is deliberately deterministic and does not
    assign medical diagnoses or make clinical decisions.

    It only compares explicit restrictions with exercise-demand
    metadata.
    """

    if not isinstance(exercise, dict):
        raise TypeError(
            "exercise must be a dictionary."
        )

    if not isinstance(
        restrictions,
        FunctionalRestrictions,
    ):
        raise TypeError(
            "restrictions must be FunctionalRestrictions."
        )

    restrictions.validate()

    reasons: list[str] = []

    # ---------------------------------------------------------
    # Numeric demand limits
    # ---------------------------------------------------------

    numeric_rules = (
        (
            "impact_level",
            restrictions.max_impact_level,
            "impact exceeds allowed level",
        ),
        (
            "knee_flexion_level",
            restrictions.max_knee_flexion_level,
            "knee-flexion demand exceeds allowed level",
        ),
        (
            "hip_load_level",
            restrictions.max_hip_load_level,
            "hip-load demand exceeds allowed level",
        ),
        (
            "back_load_level",
            restrictions.max_back_load_level,
            "back-load demand exceeds allowed level",
        ),
        (
            "ankle_load_level",
            restrictions.max_ankle_load_level,
            "ankle-load demand exceeds allowed level",
        ),
    )

    for field_name, maximum, reason in numeric_rules:
        if maximum is None:
            continue

        exercise_value = exercise.get(field_name)

        if exercise_value is None:
            reasons.append(
                f"missing exercise metadata: {field_name}"
            )
            continue

        if exercise_value > maximum:
            reasons.append(reason)

    # ---------------------------------------------------------
    # Boolean functional restrictions
    # ---------------------------------------------------------

    if restrictions.avoid_overhead_shoulder:
        if exercise.get(
            "shoulder_overhead_required",
            False,
        ):
            reasons.append(
                "requires overhead shoulder movement"
            )

    if restrictions.avoid_wrist_weight_bearing:
        if exercise.get(
            "wrist_weight_bearing",
            False,
        ):
            reasons.append(
                "requires wrist weight-bearing"
            )

    if restrictions.avoid_floor_exercises:
        if exercise.get(
            "floor_required",
            False,
        ):
            reasons.append(
                "requires floor position"
            )

    if restrictions.avoid_single_leg:
        if exercise.get(
            "single_leg",
            False,
        ):
            reasons.append(
                "requires single-leg stance"
            )

    return EligibilityDecision(
        eligible=not reasons,
        reasons=tuple(reasons),
    )


def filter_by_functional_restrictions(
    exercises: list[dict[str, Any]],
    restrictions: FunctionalRestrictions,
) -> list[dict[str, Any]]:
    """
    Return only exercises that satisfy the restrictions.
    """

    if not isinstance(exercises, list):
        raise TypeError(
            "exercises must be a list."
        )

    restrictions.validate()

    eligible: list[dict[str, Any]] = []

    for exercise in exercises:
        decision = evaluate_exercise(
            exercise,
            restrictions,
        )

        if decision.eligible:
            eligible.append(exercise)

    return eligible
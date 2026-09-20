from rules.dosage_validator import ValidatedDosage
from data.dosage_config import get_dosage_constraints


def progress_dosage(
    dosage: ValidatedDosage,
    week_number: int,
) -> ValidatedDosage:
    """
    Calculate the dosage for a future week from a validated Week-1 dosage.

    Week 1 returns the original dosage.
    Weeks 2-4 apply deterministic progression while respecting
    exercise-specific dosage constraints.
    """

    if not isinstance(dosage, ValidatedDosage):
        raise TypeError("dosage must be a ValidatedDosage.")

    if week_number not in {1, 2, 3, 4}:
        raise ValueError("week_number must be between 1 and 4.")

    if week_number == 1:
        return dosage

    constraints = get_dosage_constraints(dosage.exercise_id)

    sets = dosage.sets
    reps = dosage.reps
    duration_seconds = dosage.duration_seconds

    # Progressive set increase.
    if week_number >= 2:
        sets += 1

    # Progressive rep/time increase.
    if reps is not None:
        reps += 2

    if duration_seconds is not None:
        duration_seconds += 10

    # Respect exercise-specific bounds.
    sets = min(sets, constraints.max_sets)

    if constraints.measurement_type == "reps":
        reps = min(reps, constraints.max_reps)

    elif constraints.measurement_type == "time":
        duration_seconds = min(
            duration_seconds,
            constraints.max_duration_seconds,
        )

    return ValidatedDosage(
        exercise_id=dosage.exercise_id,
        sets=sets,
        reps=reps,
        duration_seconds=duration_seconds,
    )
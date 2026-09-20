from rules.dosage_validator import ValidatedDosage
from data.dosage_config import get_dosage_constraints


def progress_dosage_by_exposure(
    dosage: ValidatedDosage,
    exposure_number: int,
) -> ValidatedDosage:
    """
    Progress an exercise cumulatively according to its exposure number.

    Repetition-based exercises:
        Exposure 1 -> base dosage
        Exposure 2 -> +1 rep
        Exposure 3 -> +1 rep
        Exposure 4 -> +2 reps, +1 set
        Exposure 5 -> +2 reps, +1 set
        Exposure 6 -> +3 reps, +1 set
        ...

    Time-based exercises:
        Exposure 1 -> base dosage
        Exposure 2 -> +5 seconds
        Exposure 3 -> +5 seconds
        Exposure 4 -> +10 seconds, +1 set
        Exposure 5 -> +10 seconds, +1 set
        Exposure 6 -> +15 seconds, +1 set
        ...

    Progression is calculated from the original Week-1 dosage,
    so it is deterministic and does not oscillate.

    All values are capped by the exercise-specific dosage
    constraints.
    """

    if not isinstance(dosage, ValidatedDosage):
        raise TypeError("dosage must be a ValidatedDosage.")

    if not isinstance(exposure_number, int):
        raise TypeError("exposure_number must be an integer.")

    if exposure_number < 1:
        raise ValueError("exposure_number must be at least 1.")

    constraints = get_dosage_constraints(
        dosage.exercise_id
    )

    # Start from the original Week-1 dosage.
    sets = dosage.sets
    reps = dosage.reps
    duration_seconds = dosage.duration_seconds

    # ---------------------------------------------------------
    # Rep/time progression
    # ---------------------------------------------------------
    #
    # Exposure 1 -> 0 increments
    # Exposure 2 -> 1 increment
    # Exposure 3 -> 1 increment
    # Exposure 4 -> 2 increments
    # Exposure 5 -> 2 increments
    # Exposure 6 -> 3 increments
    #
    progression_steps = exposure_number // 2

    if constraints.measurement_type == "reps":
        if reps is None:
            raise ValueError(
                f"Exercise '{dosage.exercise_id}' requires reps."
            )

        reps += progression_steps

    elif constraints.measurement_type == "time":
        if duration_seconds is None:
            raise ValueError(
                f"Exercise '{dosage.exercise_id}' "
                "requires duration_seconds."
            )

        duration_seconds += progression_steps * 5

    else:
        raise ValueError(
            f"Unsupported measurement type: "
            f"{constraints.measurement_type}"
        )

    # ---------------------------------------------------------
    # Set progression
    # ---------------------------------------------------------
    #
    # Exposure 1-3  -> +0 sets
    # Exposure 4-7  -> +1 set
    # Exposure 8-11 -> +2 sets
    # Exposure 12-15 -> +3 sets
    # ...
    #
    # The configured max_sets will still cap the result.
    set_progression_steps = exposure_number // 4

    sets += set_progression_steps

    # ---------------------------------------------------------
    # Hard safety/configuration limits
    # ---------------------------------------------------------

    sets = min(
        sets,
        constraints.max_sets,
    )

    if constraints.measurement_type == "reps":
        reps = min(
            reps,
            constraints.max_reps,
        )

    elif constraints.measurement_type == "time":
        duration_seconds = min(
            duration_seconds,
            constraints.max_duration_seconds,
        )

    # ---------------------------------------------------------
    # Return validated dosage
    # ---------------------------------------------------------

    return ValidatedDosage(
        exercise_id=dosage.exercise_id,
        sets=sets,
        reps=reps,
        duration_seconds=duration_seconds,
    )
from data.exercise_catalog import EXERCISES


REQUIRED_FIELDS = {
    "id",
    "name",
    "category",
    "difficulty",
    "measurement_type",
    "progression_group",
    "stationary",
    "cv_detectable",
    "camera_view",
    "required_landmarks",
    "impact_level",
    "knee_flexion_level",
    "hip_load_level",
    "shoulder_overhead_required",
    "wrist_weight_bearing",
    "back_load_level",
    "ankle_load_level",
    "floor_required",
    "single_leg",
}


VALID_CATEGORIES = {
    "cardio",
    "lower_body",
    "upper_body",
    "core",
}


VALID_MEASUREMENT_TYPES = {
    "reps",
    "time",
}


def validate_catalog() -> None:
    if len(EXERCISES) != 18:
        raise AssertionError(
            f"Expected 18 exercises, got {len(EXERCISES)}."
        )

    ids = [
        exercise["id"]
        for exercise in EXERCISES
    ]

    if len(ids) != len(set(ids)):
        raise AssertionError(
            "Duplicate exercise IDs found."
        )

    for exercise in EXERCISES:

        missing = REQUIRED_FIELDS - exercise.keys()

        if missing:
            raise AssertionError(
                f"{exercise.get('id', '<unknown>')} "
                f"is missing fields: {sorted(missing)}"
            )

        if exercise["category"] not in VALID_CATEGORIES:
            raise AssertionError(
                f"{exercise['id']}: invalid category "
                f"{exercise['category']!r}"
            )

        if exercise["measurement_type"] not in VALID_MEASUREMENT_TYPES:
            raise AssertionError(
                f"{exercise['id']}: invalid measurement_type "
                f"{exercise['measurement_type']!r}"
            )

        if not 1 <= exercise["difficulty"] <= 5:
            raise AssertionError(
                f"{exercise['id']}: difficulty must be 1–5."
            )

        for field in (
            "impact_level",
            "knee_flexion_level",
            "hip_load_level",
            "back_load_level",
            "ankle_load_level",
        ):
            value = exercise[field]

            if not isinstance(value, int):
                raise AssertionError(
                    f"{exercise['id']}: {field} must be int."
                )

            if not 0 <= value <= 3:
                raise AssertionError(
                    f"{exercise['id']}: {field} must be between 0 and 3."
                )

        for field in (
            "stationary",
            "cv_detectable",
            "shoulder_overhead_required",
            "wrist_weight_bearing",
            "floor_required",
            "single_leg",
        ):
            if not isinstance(exercise[field], bool):
                raise AssertionError(
                    f"{exercise['id']}: {field} must be bool."
                )

        if not isinstance(exercise["required_landmarks"], list):
            raise AssertionError(
                f"{exercise['id']}: required_landmarks "
                f"must be a list."
            )

    print("EXERCISE CATALOG VALIDATION SUCCESSFUL")
    print(f"Exercises validated: {len(EXERCISES)}")


if __name__ == "__main__":
    validate_catalog()
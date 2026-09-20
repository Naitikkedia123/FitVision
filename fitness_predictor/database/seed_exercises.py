from data.exercise_catalog import EXERCISES
from database.client import get_supabase_admin_client


def build_database_exercises() -> list[dict]:
    """
    Convert the Python exercise catalogue into the exact structure
    required by the Supabase exercises table.
    """

    database_exercises: list[dict] = []

    required_fields = [
        "id",
        "name",
        "category",
        "difficulty",
        "measurement_type",
        "progression_group",
        "impact_level",
        "knee_flexion_level",
        "hip_load_level",
        "shoulder_overhead_required",
        "wrist_weight_bearing",
        "back_load_level",
        "ankle_load_level",
        "floor_required",
        "single_leg",
    ]

    for index, exercise in enumerate(EXERCISES):
        missing_fields = [
            field
            for field in required_fields
            if field not in exercise
        ]

        if missing_fields:
            raise ValueError(
                f"Exercise at index {index} "
                f"({exercise.get('id', '<unknown>')}) is missing "
                f"fields: {missing_fields}"
            )

        measurement_type = exercise["measurement_type"]

        if measurement_type not in {
            "reps",
            "time",
        }:
            raise ValueError(
                f"Invalid measurement_type for "
                f"{exercise['id']}: {measurement_type!r}"
            )

        for field in (
            "impact_level",
            "knee_flexion_level",
            "hip_load_level",
            "back_load_level",
            "ankle_load_level",
        ):
            value = exercise[field]

            if not isinstance(value, int) or not 0 <= value <= 3:
                raise ValueError(
                    f"{exercise['id']}: {field} must be "
                    f"an integer between 0 and 3."
                )

        for field in (
            "shoulder_overhead_required",
            "wrist_weight_bearing",
            "floor_required",
            "single_leg",
            "stationary",
            "cv_detectable",
        ):
            if not isinstance(exercise[field], bool):
                raise ValueError(
                    f"{exercise['id']}: {field} must be boolean."
                )

        database_exercises.append(
            {
                "id": exercise["id"],
                "name": exercise["name"],
                "category": exercise["category"],
                "difficulty": exercise["difficulty"],
                "measurement_type": exercise["measurement_type"],
                "progression_group": exercise["progression_group"],
                "stationary": exercise["stationary"],
                "cv_detectable": exercise["cv_detectable"],
                "camera_view": exercise.get("camera_view"),
                "required_landmarks": exercise.get(
                    "required_landmarks",
                    [],
                ),

                # Functional-demand metadata
                "impact_level": exercise["impact_level"],
                "knee_flexion_level": exercise["knee_flexion_level"],
                "hip_load_level": exercise["hip_load_level"],
                "shoulder_overhead_required": (
                    exercise[
                        "shoulder_overhead_required"
                    ]
                ),
                "wrist_weight_bearing": (
                    exercise[
                        "wrist_weight_bearing"
                    ]
                ),
                "back_load_level": exercise[
                    "back_load_level"
                ],
                "ankle_load_level": exercise[
                    "ankle_load_level"
                ],
                "floor_required": exercise[
                    "floor_required"
                ],
                "single_leg": exercise[
                    "single_leg"
                ],

                "active": True,
            }
        )

    return database_exercises


def seed_exercises() -> None:
    """
    Insert/update all exercise records in Supabase.

    Uses the admin client because exercise definitions are
    trusted master data and the public application should not
    be able to modify them.
    """

    exercises = build_database_exercises()

    if not exercises:
        raise RuntimeError(
            "No exercises found in EXERCISES."
        )

    supabase = get_supabase_admin_client()

    response = (
        supabase
        .table("exercises")
        .upsert(
            exercises,
            on_conflict="id",
        )
        .execute()
    )

    saved = response.data or []

    if len(saved) != len(exercises):
        raise RuntimeError(
            f"Expected {len(exercises)} exercises to be saved, "
            f"but Supabase returned {len(saved)}."
        )

    print("EXERCISE SEED SUCCESSFUL")
    print(f"Exercises saved: {len(saved)}")

    for exercise in saved:
        print(
            f"- {exercise['id']} | "
            f"{exercise['name']} | "
            f"{exercise['category']} | "
            f"difficulty={exercise['difficulty']}"
        )


if __name__ == "__main__":
    seed_exercises()
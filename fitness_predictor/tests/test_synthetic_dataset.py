from data.exercise_catalog import EXERCISES
from ml.synthetic_dataset import generate_synthetic_dataset


def main():
    exercises = EXERCISES

    dataset = generate_synthetic_dataset(
        exercises=exercises,
        n_users=10,
    )

    assert len(dataset) == 10 * len(exercises)
    assert len(dataset) == 180

    required_fields = {
        "user_index",
        "age",
        "height_cm",
        "weight_kg",
        "bmi",
        "fitness_level",
        "activity_level",
        "workout_time_min",
        "goal",
        "individual_ability",
        "exercise_id",
        "difficulty",
        "impact_level",
        "knee_flexion_level",
        "hip_load_level",
        "shoulder_overhead_required",
        "wrist_weight_bearing",
        "back_load_level",
        "ankle_load_level",
        "floor_required",
        "single_leg",
        "measurement_type",
        "target_sets",
        "target_reps",
        "target_duration_seconds",
    }

    for row in dataset:
        assert required_fields.issubset(row.keys())

        # User feature validation
        assert 18 <= row["age"] <= 65
        assert row["height_cm"] > 0
        assert row["weight_kg"] > 0
        assert row["bmi"] > 0
        assert 1 <= row["fitness_level"] <= 5
        assert 1 <= row["activity_level"] <= 5
        assert row["workout_time_min"] in {15, 20, 30, 45}

        # Synthetic personalization features
        assert row["goal"] in {
            "general_fitness",
            "endurance",
            "strength",
        }

        assert 0.85 <= row["individual_ability"] <= 1.15

        # Target validation
        assert row["target_sets"] > 0

        if row["measurement_type"] == "reps":
            assert row["target_reps"] is not None
            assert row["target_reps"] > 0
            assert row["target_duration_seconds"] is None

        elif row["measurement_type"] == "time":
            assert row["target_reps"] is None
            assert row["target_duration_seconds"] is not None
            assert row["target_duration_seconds"] > 0

        else:
            raise AssertionError(
                f"Unsupported measurement type: "
                f"{row['measurement_type']}"
            )

    # Ensure every catalog exercise appears in the dataset.
    exercise_ids = {
        row["exercise_id"]
        for row in dataset
    }

    expected_exercise_ids = {
        exercise["id"]
        for exercise in exercises
    }

    assert exercise_ids == expected_exercise_ids

    # Ensure every synthetic user has all exercises.
    for user_index in range(10):
        user_rows = [
            row
            for row in dataset
            if row["user_index"] == user_index
        ]

        assert len(user_rows) == len(exercises)

    print("SYNTHETIC DATASET TESTS PASSED ✅")
    print(f"Exercises: {len(exercises)}")
    print("Users: 10")
    print(f"Rows: {len(dataset)}")


if __name__ == "__main__":
    main()
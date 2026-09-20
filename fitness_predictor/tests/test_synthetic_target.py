import random

from ml.synthetic_target import generate_synthetic_target


def main():
    rng = random.Random(42)

    beginner = generate_synthetic_target(
        age=25,
        height_cm=170,
        weight_kg=65,
        fitness_level=1,
        activity_level=1,
        workout_time_min=15,
        goal="general_fitness",
        individual_ability=0.90,
        exercise_difficulty=1,
        impact_level=0,
        knee_flexion_level=0,
        hip_load_level=0,
        shoulder_overhead_required=False,
        wrist_weight_bearing=False,
        back_load_level=0,
        ankle_load_level=0,
        floor_required=False,
        single_leg=False,
        measurement_type="reps",
        rng=rng,
    )

    advanced = generate_synthetic_target(
        age=25,
        height_cm=170,
        weight_kg=65,
        fitness_level=5,
        activity_level=5,
        workout_time_min=45,
        goal="strength",
        individual_ability=1.10,
        exercise_difficulty=1,
        impact_level=0,
        knee_flexion_level=0,
        hip_load_level=0,
        shoulder_overhead_required=False,
        wrist_weight_bearing=False,
        back_load_level=0,
        ankle_load_level=0,
        floor_required=False,
        single_leg=False,
        measurement_type="reps",
        rng=rng,
    )

    difficult_time_exercise = generate_synthetic_target(
        age=50,
        height_cm=170,
        weight_kg=80,
        fitness_level=3,
        activity_level=3,
        workout_time_min=30,
        goal="general_fitness",
        individual_ability=1.00,
        exercise_difficulty=4,
        impact_level=1,
        knee_flexion_level=0,
        hip_load_level=0,
        shoulder_overhead_required=False,
        wrist_weight_bearing=True,
        back_load_level=2,
        ankle_load_level=0,
        floor_required=True,
        single_leg=False,
        measurement_type="time",
        rng=rng,
    )

    assert beginner.reps is not None
    assert beginner.duration_seconds is None

    assert advanced.reps is not None
    assert advanced.duration_seconds is None

    assert advanced.reps > beginner.reps
    assert advanced.sets > beginner.sets

    assert difficult_time_exercise.duration_seconds is not None
    assert difficult_time_exercise.reps is None

    print("IMPROVED SYNTHETIC TARGET TESTS PASSED ✅")
    print(f"Beginner: {beginner}")
    print(f"Advanced: {advanced}")
    print(f"Time exercise: {difficult_time_exercise}")


if __name__ == "__main__":
    main()
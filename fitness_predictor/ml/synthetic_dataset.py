import random
from typing import Any

from ml.synthetic_target import generate_synthetic_target


RANDOM_SEED = 42


def _generate_user_profile(
    user_index: int,
    rng: random.Random,
) -> dict[str, Any]:
    age = rng.randint(18, 65)
    height_cm = round(rng.uniform(150, 195), 1)
    weight_kg = round(rng.uniform(45, 110), 1)

    fitness_level = rng.randint(1, 5)
    activity_level = rng.randint(1, 5)
    workout_time_min = rng.choice([15, 20, 30, 45])

    goal = rng.choice(
        [
            "general_fitness",
            "endurance",
            "strength",
        ]
    )

    # Persistent individual ability for this synthetic user.
    # This value is kept constant across all 18 exercises.
    individual_ability = round(
        rng.uniform(0.85, 1.15),
        4,
    )

    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2)

    return {
        "user_index": user_index,
        "age": age,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": round(bmi, 2),
        "fitness_level": fitness_level,
        "activity_level": activity_level,
        "workout_time_min": workout_time_min,
        "goal": goal,
        "individual_ability": individual_ability,
    }


def generate_synthetic_dataset(
    exercises: list[dict[str, Any]],
    n_users: int = 10_000,
) -> list[dict[str, Any]]:
    """
    Generate a synthetic ML training dataset.

    Each synthetic user receives one persistent profile and
    one row per exercise.

    This dataset is for prototype/model-development purposes
    and is not a medically validated prescription dataset.
    """

    if not isinstance(exercises, list):
        raise TypeError("exercises must be a list.")

    if not exercises:
        raise ValueError("exercises cannot be empty.")

    if n_users <= 0:
        raise ValueError("n_users must be greater than 0.")

    rng = random.Random(RANDOM_SEED)

    rows: list[dict[str, Any]] = []

    for user_index in range(n_users):
        user = _generate_user_profile(
            user_index=user_index,
            rng=rng,
        )

        for exercise in exercises:
            measurement_type = exercise["measurement_type"]

            target = generate_synthetic_target(
                age=user["age"],
                height_cm=user["height_cm"],
                weight_kg=user["weight_kg"],
                fitness_level=user["fitness_level"],
                activity_level=user["activity_level"],
                workout_time_min=user["workout_time_min"],
                goal=user["goal"],
                individual_ability=user["individual_ability"],
                exercise_difficulty=exercise["difficulty"],
                impact_level=exercise["impact_level"],
                knee_flexion_level=exercise["knee_flexion_level"],
                hip_load_level=exercise["hip_load_level"],
                shoulder_overhead_required=exercise[
                    "shoulder_overhead_required"
                ],
                wrist_weight_bearing=exercise[
                    "wrist_weight_bearing"
                ],
                back_load_level=exercise["back_load_level"],
                ankle_load_level=exercise["ankle_load_level"],
                floor_required=exercise["floor_required"],
                single_leg=exercise["single_leg"],
                measurement_type=measurement_type,
                rng=rng,
            )

            rows.append(
                {
                    # User features
                    "user_index": user["user_index"],
                    "age": user["age"],
                    "height_cm": user["height_cm"],
                    "weight_kg": user["weight_kg"],
                    "bmi": user["bmi"],
                    "fitness_level": user["fitness_level"],
                    "activity_level": user["activity_level"],
                    "workout_time_min": user["workout_time_min"],
                    "goal": user["goal"],
                    "individual_ability": user[
                        "individual_ability"
                    ],

                    # Exercise identity
                    "exercise_id": exercise["id"],

                    # Exercise features
                    "difficulty": exercise["difficulty"],
                    "impact_level": exercise["impact_level"],
                    "knee_flexion_level": exercise[
                        "knee_flexion_level"
                    ],
                    "hip_load_level": exercise["hip_load_level"],
                    "shoulder_overhead_required": int(
                        exercise["shoulder_overhead_required"]
                    ),
                    "wrist_weight_bearing": int(
                        exercise["wrist_weight_bearing"]
                    ),
                    "back_load_level": exercise["back_load_level"],
                    "ankle_load_level": exercise["ankle_load_level"],
                    "floor_required": int(
                        exercise["floor_required"]
                    ),
                    "single_leg": int(
                        exercise["single_leg"]
                    ),

                    # Measurement
                    "measurement_type": measurement_type,

                    # Targets
                    "target_sets": target.sets,
                    "target_reps": target.reps,
                    "target_duration_seconds": (
                        target.duration_seconds
                    ),
                }
            )

    return rows
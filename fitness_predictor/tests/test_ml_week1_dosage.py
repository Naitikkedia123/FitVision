from models.user_profile import UserProfile
from ml.ml_predictor import MLDosagePredictor
from services.week1_dosage_service import Week1DosageService


def main():
    user = UserProfile(
        age=20,
        sex="male",
        height_cm=175,
        weight_kg=70,
        fitness_level=4,
        activity_level=4,
        goal="general_fitness",
        workout_time_min=30,
        user_id="test-user",
    )

    exercises = [
        {
            "id": "bodyweight_squat",
            "difficulty": 2,
            "measurement_type": "reps",
            "impact_level": 0,
            "knee_flexion_level": 2,
            "hip_load_level": 2,
            "shoulder_overhead_required": False,
            "wrist_weight_bearing": False,
            "back_load_level": 1,
            "ankle_load_level": 1,
            "floor_required": False,
            "single_leg": False,
        },
        {
            "id": "plank",
            "difficulty": 3,
            "measurement_type": "time",
            "impact_level": 0,
            "knee_flexion_level": 0,
            "hip_load_level": 0,
            "shoulder_overhead_required": False,
            "wrist_weight_bearing": True,
            "back_load_level": 2,
            "ankle_load_level": 0,
            "floor_required": True,
            "single_leg": False,
        },
    ]

    ml_predictor = MLDosagePredictor()

    service = Week1DosageService(
        predictor=ml_predictor
    )

    dosages = service.generate(
        user=user,
        exercises=exercises,
    )

    assert len(dosages) == 2

    squat = dosages[0]
    plank = dosages[1]

    # Validator should return integer, bounded values.
    assert squat.exercise_id == "bodyweight_squat"
    assert isinstance(squat.sets, int)
    assert isinstance(squat.reps, int)
    assert squat.duration_seconds is None

    assert plank.exercise_id == "plank"
    assert isinstance(plank.sets, int)
    assert plank.reps is None
    assert isinstance(plank.duration_seconds, int)

    assert squat.sets >= 1
    assert squat.reps >= 1

    assert plank.sets >= 1
    assert plank.duration_seconds >= 1

    print("ML → VALIDATOR INTEGRATION TEST PASSED ✅")

    print(
        f"Squat validated dosage: "
        f"{squat.sets} sets × {squat.reps} reps"
    )

    print(
        f"Plank validated dosage: "
        f"{plank.sets} sets × "
        f"{plank.duration_seconds}s"
    )


if __name__ == "__main__":
    main()
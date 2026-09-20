from models.user_profile import UserProfile
from ml.ml_predictor import MLDosagePredictor


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

    predictor = MLDosagePredictor()

    rep_exercise = {
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
    }

    time_exercise = {
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
    }

    rep_prediction = predictor.predict(
        user,
        rep_exercise,
    )

    time_prediction = predictor.predict(
        user,
        time_exercise,
    )

    assert rep_prediction.exercise_id == "bodyweight_squat"
    assert rep_prediction.sets > 0
    assert rep_prediction.reps is not None
    assert rep_prediction.reps > 0
    assert rep_prediction.duration_seconds is None

    assert time_prediction.exercise_id == "plank"
    assert time_prediction.sets > 0
    assert time_prediction.reps is None
    assert time_prediction.duration_seconds is not None
    assert time_prediction.duration_seconds > 0

    print("ML PREDICTOR TESTS PASSED ✅")
    print(
        f"Squat prediction: "
        f"sets={rep_prediction.sets:.3f}, "
        f"reps={rep_prediction.reps:.3f}"
    )
    print(
        f"Plank prediction: "
        f"sets={time_prediction.sets:.3f}, "
        f"time={time_prediction.duration_seconds:.3f}s"
    )


if __name__ == "__main__":
    main()
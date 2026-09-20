from models.user_profile import UserProfile
from ml.baseline_predictor import BaselineDosagePredictor


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
    )

    predictor = BaselineDosagePredictor()

    rep_exercise = {
        "id": "bodyweight_squat",
        "measurement_type": "reps",
    }

    time_exercise = {
        "id": "plank",
        "measurement_type": "time",
    }

    rep_prediction = predictor.predict(user, rep_exercise)
    time_prediction = predictor.predict(user, time_exercise)

    assert rep_prediction.exercise_id == "bodyweight_squat"
    assert rep_prediction.sets == 3.0
    assert rep_prediction.reps == 12.0
    assert rep_prediction.duration_seconds is None

    assert time_prediction.exercise_id == "plank"
    assert time_prediction.sets == 3.0
    assert time_prediction.reps is None
    assert time_prediction.duration_seconds == 30.0

    print("BASELINE PREDICTOR TESTS PASSED ✅")


if __name__ == "__main__":
    main()
from ml.prediction import DosagePrediction
from rules.dosage_validator import validate_prediction
from planning.dosage_progression import progress_dosage


def main():
    squat_prediction = DosagePrediction(
        exercise_id="bodyweight_squat",
        sets=3.0,
        reps=12.0,
    )

    squat_week1 = validate_prediction(squat_prediction)

    squat_week2 = progress_dosage(
        squat_week1,
        week_number=2,
    )

    squat_week3 = progress_dosage(
        squat_week1,
        week_number=3,
    )

    squat_week4 = progress_dosage(
        squat_week1,
        week_number=4,
    )

    assert squat_week1.sets == 3
    assert squat_week1.reps == 12

    assert squat_week2.sets == 3
    assert squat_week2.reps == 14

    assert squat_week3.sets == 3
    assert squat_week3.reps == 14

    assert squat_week4.sets == 3
    assert squat_week4.reps == 14

    plank_prediction = DosagePrediction(
        exercise_id="plank",
        sets=3.0,
        duration_seconds=30.0,
    )

    plank_week1 = validate_prediction(plank_prediction)

    plank_week2 = progress_dosage(
        plank_week1,
        week_number=2,
    )

    assert plank_week2.sets == 3
    assert plank_week2.duration_seconds == 40

    print("DOSAGE PROGRESSION TESTS PASSED ✅")


if __name__ == "__main__":
    main()
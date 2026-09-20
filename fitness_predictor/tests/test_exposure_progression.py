from ml.prediction import DosagePrediction
from rules.dosage_validator import validate_prediction
from planning.exposure_progression import (
    progress_dosage_by_exposure,
)


def main():
    squat_prediction = DosagePrediction(
        exercise_id="bodyweight_squat",
        sets=2.0,
        reps=12.0,
    )

    squat = validate_prediction(
        squat_prediction
    )

    exposure_1 = progress_dosage_by_exposure(
        squat,
        exposure_number=1,
    )

    exposure_2 = progress_dosage_by_exposure(
        squat,
        exposure_number=2,
    )

    exposure_3 = progress_dosage_by_exposure(
        squat,
        exposure_number=3,
    )

    exposure_4 = progress_dosage_by_exposure(
        squat,
        exposure_number=4,
    )

    exposure_5 = progress_dosage_by_exposure(
        squat,
        exposure_number=5,
    )

    exposure_6 = progress_dosage_by_exposure(
        squat,
        exposure_number=6,
    )

    # Exposure 1: original ML dosage
    assert exposure_1.sets == 2
    assert exposure_1.reps == 12

    # Exposure 2: +1 rep
    assert exposure_2.sets == 2
    assert exposure_2.reps == 13

    # Exposure 3: stays at previous progression
    assert exposure_3.sets == 2
    assert exposure_3.reps == 13

    # Exposure 4: +1 rep and +1 set
    assert exposure_4.sets == 3
    assert exposure_4.reps == 14

    # Exposure 5: stays at previous progression
    assert exposure_5.sets == 3
    assert exposure_5.reps == 14

    # Exposure 6: +1 rep
    assert exposure_6.sets == 3
    assert exposure_6.reps == 15

    plank_prediction = DosagePrediction(
        exercise_id="plank",
        sets=2.0,
        duration_seconds=30.0,
    )

    plank = validate_prediction(
        plank_prediction
    )

    plank_exposure_2 = progress_dosage_by_exposure(
        plank,
        exposure_number=2,
    )

    plank_exposure_4 = progress_dosage_by_exposure(
        plank,
        exposure_number=4,
    )

    assert plank_exposure_2.sets == 2
    assert plank_exposure_2.duration_seconds == 35

    assert plank_exposure_4.sets == 3
    assert plank_exposure_4.duration_seconds == 40

    print("EXPOSURE PROGRESSION TESTS PASSED ✅")


if __name__ == "__main__":
    main()
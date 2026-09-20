from ml.prediction import DosagePrediction
from rules.dosage_validator import validate_prediction


def main() -> None:
    # ---------------------------------------------------------
    # Normal reps prediction
    # ---------------------------------------------------------

    squat = DosagePrediction(
        exercise_id="bodyweight_squat",
        sets=2.6,
        reps=12.4,
    )

    result = validate_prediction(squat)

    assert result.sets == 3
    assert result.reps == 12
    assert result.duration_seconds is None

    # ---------------------------------------------------------
    # Normal time prediction
    # ---------------------------------------------------------

    plank = DosagePrediction(
        exercise_id="plank",
        sets=2.2,
        duration_seconds=31.6,
    )

    result = validate_prediction(plank)

    assert result.sets == 2
    assert result.duration_seconds == 32
    assert result.reps is None

    # ---------------------------------------------------------
    # Excessive reps should be clamped
    # ---------------------------------------------------------

    excessive = DosagePrediction(
        exercise_id="bodyweight_squat",
        sets=10,
        reps=500,
    )

    result = validate_prediction(excessive)

    assert result.sets == 3
    assert result.reps == 15

    # ---------------------------------------------------------
    # Negative prediction should be clamped to valid minimum
    # ---------------------------------------------------------

    negative = DosagePrediction(
        exercise_id="bodyweight_squat",
        sets=-4,
        reps=-20,
    )

    result = validate_prediction(negative)

    assert result.sets == 1
    assert result.reps == 6

    # ---------------------------------------------------------
    # Wrong measurement type should fail
    # ---------------------------------------------------------

    try:
        validate_prediction(
            DosagePrediction(
                exercise_id="plank",
                sets=2,
                reps=10,
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Plank incorrectly accepted a reps prediction."
        )

    # ---------------------------------------------------------
    # NaN should fail
    # ---------------------------------------------------------

    try:
        validate_prediction(
            DosagePrediction(
                exercise_id="bodyweight_squat",
                sets=float("nan"),
                reps=10,
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "NaN prediction was incorrectly accepted."
        )

    print("DOSAGE VALIDATOR TESTS PASSED ✅")


if __name__ == "__main__":
    main()
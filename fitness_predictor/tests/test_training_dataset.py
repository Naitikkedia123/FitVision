from data.exercise_catalog import EXERCISES
from ml.synthetic_dataset import generate_synthetic_dataset
from ml.training_dataset import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    prepare_training_data,
)


def main():
    dataset = generate_synthetic_dataset(
        exercises=EXERCISES,
        n_users=10,
    )

    prepared = prepare_training_data(dataset)

    assert len(prepared.features) == 180
    assert len(prepared.target_sets) == 180
    assert len(prepared.target_reps) == 180
    assert len(prepared.target_duration_seconds) == 180
    assert len(prepared.measurement_type) == 180

    expected_feature_count = (
        len(NUMERIC_FEATURES)
        + len(CATEGORICAL_FEATURES)
    )

    assert prepared.features.shape[1] == expected_feature_count

    # Numeric features must be present.
    for feature in NUMERIC_FEATURES:
        assert feature in prepared.features.columns

    # Categorical features must also be present.
    for feature in CATEGORICAL_FEATURES:
        assert feature in prepared.features.columns

    # Hidden synthetic variable must NOT be used by the model.
    assert "individual_ability" not in prepared.features.columns

    assert "target_sets" not in prepared.features.columns
    assert "target_reps" not in prepared.features.columns
    assert "target_duration_seconds" not in prepared.features.columns

    assert set(prepared.measurement_type.unique()) == {
        "reps",
        "time",
    }

    assert set(prepared.features["goal"].unique()).issubset(
        {
            "general_fitness",
            "endurance",
            "strength",
        }
    )

    assert set(prepared.features["exercise_id"].unique()) == {
        exercise["id"]
        for exercise in EXERCISES
    }

    print("TRAINING DATA PREPARATION TESTS PASSED ✅")
    print(f"Rows: {len(prepared.features)}")
    print(
        f"Numeric features: {len(NUMERIC_FEATURES)}"
    )
    print(
        f"Categorical features: {len(CATEGORICAL_FEATURES)}"
    )
    print(
        f"Total features: {prepared.features.shape[1]}"
    )
    print(
        f"Reps targets: "
        f"{prepared.target_reps.notna().sum()}"
    )
    print(
        f"Duration targets: "
        f"{prepared.target_duration_seconds.notna().sum()}"
    )


if __name__ == "__main__":
    main()
from pathlib import Path

import joblib
import pandas as pd

from sklearn.metrics import mean_absolute_error, mean_squared_error

from ml.training_split import split_by_user


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "training"
    / "synthetic_training_data.csv"
)

MODEL_PATHS = {
    "sets": PROJECT_ROOT / "models" / "sets_model.joblib",
    "reps": PROJECT_ROOT / "models" / "reps_model.joblib",
    "duration": PROJECT_ROOT / "models" / "duration_model.joblib",
}

TARGET_COLUMNS = {
    "sets": "target_sets",
    "reps": "target_reps",
    "duration": "target_duration_seconds",
}


def evaluate_model(
    model_name: str,
    test_df: pd.DataFrame,
) -> tuple[float, float, int]:
    model_bundle = joblib.load(
        MODEL_PATHS[model_name]
    )

    model = model_bundle["model"]
    preprocessor = model_bundle["preprocessor"]
    feature_columns = model_bundle["feature_columns"]

    target_column = TARGET_COLUMNS[model_name]

    X_test = test_df[feature_columns]
    y_test = test_df[target_column]

    if y_test.isna().any():
        raise ValueError(
            f"{model_name} test set contains missing targets."
        )

    X_test_encoded = preprocessor.transform(X_test)

    predictions = model.predict(X_test_encoded)

    mae = mean_absolute_error(
        y_test,
        predictions,
    )

    rmse = mean_squared_error(
        y_test,
        predictions,
    ) ** 0.5

    return mae, rmse, len(test_df)


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    for model_path in MODEL_PATHS.values():
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {model_path}"
            )

    dataframe = pd.read_csv(DATASET_PATH)

    if len(dataframe) != 180_000:
        raise ValueError(
            f"Expected 180000 rows, got {len(dataframe)}."
        )

    # Important: use the exact same user-level splitting logic
    # used during training.
    dataset = dataframe.to_dict(
        orient="records"
    )

    split = split_by_user(
        dataset=dataset,
        train_size=0.70,
        validation_size=0.15,
        test_size=0.15,
    )

    test_df = split.test

    print("HELD-OUT TEST EVALUATION")
    print("=" * 50)
    print(f"Test users: {test_df['user_index'].nunique()}")
    print(f"Test rows: {len(test_df)}")

    # ---------------------------------------------------------
    # Sets
    # ---------------------------------------------------------

    sets_test = test_df.copy()

    sets_mae, sets_rmse, sets_rows = evaluate_model(
        model_name="sets",
        test_df=sets_test,
    )

    print("\nSETS MODEL")
    print(f"Rows: {sets_rows}")
    print(f"MAE: {sets_mae:.4f}")
    print(f"RMSE: {sets_rmse:.4f}")

    # ---------------------------------------------------------
    # Reps
    # ---------------------------------------------------------

    reps_test = test_df[
        test_df["measurement_type"] == "reps"
    ].copy()

    reps_mae, reps_rmse, reps_rows = evaluate_model(
        model_name="reps",
        test_df=reps_test,
    )

    print("\nREPS MODEL")
    print(f"Rows: {reps_rows}")
    print(f"MAE: {reps_mae:.4f}")
    print(f"RMSE: {reps_rmse:.4f}")

    # ---------------------------------------------------------
    # Duration
    # ---------------------------------------------------------

    duration_test = test_df[
        test_df["measurement_type"] == "time"
    ].copy()

    duration_mae, duration_rmse, duration_rows = evaluate_model(
        model_name="duration",
        test_df=duration_test,
    )

    print("\nDURATION MODEL")
    print(f"Rows: {duration_rows}")
    print(f"MAE: {duration_mae:.4f}")
    print(f"RMSE: {duration_rmse:.4f}")

    print("\nTEST EVALUATION COMPLETED ✅")


if __name__ == "__main__":
    main()
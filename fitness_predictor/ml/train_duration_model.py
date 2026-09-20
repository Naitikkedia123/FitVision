from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import OneHotEncoder

from ml.training_split import split_by_user


DATASET_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "training"
    / "synthetic_training_data.csv"
)

MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "duration_model.joblib"
)

NUMERIC_FEATURES = [
    "age",
    "height_cm",
    "weight_kg",
    "bmi",
    "fitness_level",
    "activity_level",
    "workout_time_min",
    "difficulty",
    "impact_level",
    "knee_flexion_level",
    "hip_load_level",
    "shoulder_overhead_required",
    "wrist_weight_bearing",
    "back_load_level",
    "ankle_load_level",
    "floor_required",
    "single_leg",
]

CATEGORICAL_FEATURES = [
    "goal",
    "exercise_id",
    "measurement_type",
]

FEATURE_COLUMNS = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    dataframe = pd.read_csv(DATASET_PATH)

    if len(dataframe) != 180_000:
        raise ValueError(
            f"Expected 180000 rows, got {len(dataframe)}."
        )

    # Duration model only uses time-based exercises.
    dataframe = dataframe[
        dataframe["measurement_type"] == "time"
    ].copy()

    if dataframe.empty:
        raise ValueError(
            "No time-based training samples found."
        )

    dataset = dataframe.to_dict(orient="records")

    split = split_by_user(
        dataset=dataset,
        train_size=0.70,
        validation_size=0.15,
        test_size=0.15,
    )

    train_df = split.train
    validation_df = split.validation

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df["target_duration_seconds"]

    X_validation = validation_df[FEATURE_COLUMNS]
    y_validation = validation_df["target_duration_seconds"]

    if y_train.isna().any():
        raise ValueError(
            "Training data contains missing duration targets."
        )

    if y_validation.isna().any():
        raise ValueError(
            "Validation data contains missing duration targets."
        )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    X_train_encoded = preprocessor.fit_transform(
        X_train
    )

    X_validation_encoded = preprocessor.transform(
        X_validation
    )

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
        max_features="sqrt",
    )

    model.fit(
        X_train_encoded,
        y_train,
    )

    predictions = model.predict(
        X_validation_encoded
    )

    mae = mean_absolute_error(
        y_validation,
        predictions,
    )

    rmse = mean_squared_error(
        y_validation,
        predictions,
    ) ** 0.5

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        {
            "preprocessor": preprocessor,
            "model": model,
            "feature_columns": FEATURE_COLUMNS,
            "numeric_features": NUMERIC_FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
        },
        MODEL_PATH,
    )

    print("DURATION MODEL TRAINED ✅")
    print(f"Training rows: {len(train_df)}")
    print(f"Validation rows: {len(validation_df)}")
    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"Saved model: {MODEL_PATH}")


if __name__ == "__main__":
    main()
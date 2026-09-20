from dataclasses import dataclass
from typing import Any

import pandas as pd


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

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@dataclass(frozen=True)
class PreparedTrainingData:
    features: pd.DataFrame
    target_sets: pd.Series
    target_reps: pd.Series
    target_duration_seconds: pd.Series
    measurement_type: pd.Series


def prepare_training_data(
    dataset: list[dict[str, Any]],
) -> PreparedTrainingData:
    if not isinstance(dataset, list):
        raise TypeError("dataset must be a list.")

    if not dataset:
        raise ValueError("dataset cannot be empty.")

    dataframe = pd.DataFrame(dataset)

    required_columns = set(FEATURE_COLUMNS) | {
        "target_sets",
        "target_reps",
        "target_duration_seconds",
    }

    missing_columns = sorted(
        required_columns - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Dataset is missing columns: {missing_columns}"
        )

    # Make a clean copy containing only information that will
    # actually be available to the production ML predictor.
    features = dataframe[FEATURE_COLUMNS].copy()

    # Validate categorical values.
    expected_measurement_types = {"reps", "time"}

    actual_measurement_types = set(
        features["measurement_type"].dropna().unique()
    )

    unexpected_measurement_types = (
        actual_measurement_types - expected_measurement_types
    )

    if unexpected_measurement_types:
        raise ValueError(
            "Unsupported measurement types: "
            f"{sorted(unexpected_measurement_types)}"
        )

    if features["goal"].isna().any():
        raise ValueError("goal contains missing values.")

    if features["exercise_id"].isna().any():
        raise ValueError("exercise_id contains missing values.")

    # The synthetic latent variable must never reach the model.
    assert "individual_ability" not in features.columns

    target_sets = dataframe["target_sets"].copy()
    target_reps = dataframe["target_reps"].copy()
    target_duration_seconds = dataframe[
        "target_duration_seconds"
    ].copy()

    measurement_type = dataframe["measurement_type"].copy()

    return PreparedTrainingData(
        features=features,
        target_sets=target_sets,
        target_reps=target_reps,
        target_duration_seconds=target_duration_seconds,
        measurement_type=measurement_type,
    )
from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split


@dataclass(frozen=True)
class TrainingSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def split_by_user(
    dataset: list[dict[str, Any]],
    train_size: float = 0.70,
    validation_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42,
) -> TrainingSplit:
    if not isinstance(dataset, list):
        raise TypeError("dataset must be a list.")

    if not dataset:
        raise ValueError("dataset cannot be empty.")

    if abs(
        train_size + validation_size + test_size - 1.0
    ) > 1e-9:
        raise ValueError(
            "train_size + validation_size + test_size must equal 1."
        )

    if any(
        size <= 0
        for size in (
            train_size,
            validation_size,
            test_size,
        )
    ):
        raise ValueError("All split sizes must be greater than 0.")

    dataframe = pd.DataFrame(dataset)

    if "user_index" not in dataframe.columns:
        raise ValueError(
            "Dataset must contain 'user_index'."
        )

    user_ids = dataframe["user_index"].unique()

    train_users, temp_users = train_test_split(
        user_ids,
        test_size=validation_size + test_size,
        random_state=random_state,
    )

    relative_test_size = test_size / (
        validation_size + test_size
    )

    validation_users, test_users = train_test_split(
        temp_users,
        test_size=relative_test_size,
        random_state=random_state,
    )

    train = dataframe[
        dataframe["user_index"].isin(train_users)
    ].copy()

    validation = dataframe[
        dataframe["user_index"].isin(validation_users)
    ].copy()

    test = dataframe[
        dataframe["user_index"].isin(test_users)
    ].copy()

    train = train.reset_index(drop=True)
    validation = validation.reset_index(drop=True)
    test = test.reset_index(drop=True)

    return TrainingSplit(
        train=train,
        validation=validation,
        test=test,
    )
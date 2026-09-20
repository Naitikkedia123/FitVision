from pathlib import Path

import pandas as pd

from ml.training_split import split_by_user


DATASET_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "training"
    / "synthetic_training_data.csv"
)


def main():
    assert DATASET_PATH.exists(), (
        f"Training dataset not found: {DATASET_PATH}"
    )

    dataframe = pd.read_csv(DATASET_PATH)

    assert len(dataframe) == 180_000

    dataset = dataframe.to_dict(orient="records")

    split = split_by_user(
        dataset=dataset,
        train_size=0.70,
        validation_size=0.15,
        test_size=0.15,
    )

    train_users = set(split.train["user_index"])
    validation_users = set(split.validation["user_index"])
    test_users = set(split.test["user_index"])

    # No user can appear in more than one split.
    assert train_users.isdisjoint(validation_users)
    assert train_users.isdisjoint(test_users)
    assert validation_users.isdisjoint(test_users)

    # All 10,000 users must be represented exactly once.
    all_users = (
        train_users
        | validation_users
        | test_users
    )

    assert len(all_users) == 10_000

    # Every user has exactly 18 exercise rows.
    for users, split_name in (
        (train_users, "train"),
        (validation_users, "validation"),
        (test_users, "test"),
    ):
        current_split = getattr(split, split_name)

        counts = current_split["user_index"].value_counts()

        assert len(counts) == len(users)
        assert counts.min() == 18
        assert counts.max() == 18

    # Expected exact user-level split.
    assert len(train_users) == 7_000
    assert len(validation_users) == 1_500
    assert len(test_users) == 1_500

    # Expected row counts.
    assert len(split.train) == 126_000
    assert len(split.validation) == 27_000
    assert len(split.test) == 27_000

    # Total rows must be preserved.
    assert (
        len(split.train)
        + len(split.validation)
        + len(split.test)
        == 180_000
    )

    print("FULL TRAINING SPLIT TEST PASSED ✅")
    print(f"Total users: {len(all_users)}")
    print(f"Train users: {len(train_users)}")
    print(f"Validation users: {len(validation_users)}")
    print(f"Test users: {len(test_users)}")
    print(f"Train rows: {len(split.train)}")
    print(f"Validation rows: {len(split.validation)}")
    print(f"Test rows: {len(split.test)}")


if __name__ == "__main__":
    main()
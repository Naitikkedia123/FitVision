from data.exercise_catalog import EXERCISES
from ml.synthetic_dataset import generate_synthetic_dataset
from ml.training_split import split_by_user


def main():
    dataset = generate_synthetic_dataset(
        exercises=EXERCISES,
        n_users=100,
    )

    split = split_by_user(
        dataset=dataset,
        train_size=0.70,
        validation_size=0.15,
        test_size=0.15,
    )

    train_users = set(split.train["user_index"])
    validation_users = set(split.validation["user_index"])
    test_users = set(split.test["user_index"])

    assert train_users.isdisjoint(validation_users)
    assert train_users.isdisjoint(test_users)
    assert validation_users.isdisjoint(test_users)

    all_users = (
        train_users
        | validation_users
        | test_users
    )

    assert len(all_users) == 100

    assert len(split.train) == len(train_users) * 18
    assert len(split.validation) == len(validation_users) * 18
    assert len(split.test) == len(test_users) * 18

    print("TRAINING SPLIT TESTS PASSED ✅")
    print(f"Train users: {len(train_users)}")
    print(f"Validation users: {len(validation_users)}")
    print(f"Test users: {len(test_users)}")
    print(f"Train rows: {len(split.train)}")
    print(f"Validation rows: {len(split.validation)}")
    print(f"Test rows: {len(split.test)}")


if __name__ == "__main__":
    main()
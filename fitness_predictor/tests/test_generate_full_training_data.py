from data.exercise_catalog import EXERCISES
from ml.synthetic_dataset import generate_synthetic_dataset


def main():
    n_users = 10_000

    dataset = generate_synthetic_dataset(
        exercises=EXERCISES,
        n_users=n_users,
    )

    expected_rows = n_users * len(EXERCISES)

    assert len(dataset) == expected_rows
    assert len(dataset) == 180_000

    user_ids = {
        row["user_index"]
        for row in dataset
    }

    exercise_ids = {
        row["exercise_id"]
        for row in dataset
    }

    assert len(user_ids) == n_users

    assert exercise_ids == {
        exercise["id"]
        for exercise in EXERCISES
    }

    for user_index in range(n_users):
        user_rows = [
            row
            for row in dataset
            if row["user_index"] == user_index
        ]

        assert len(user_rows) == len(EXERCISES)

    print("FULL SYNTHETIC DATASET GENERATED ✅")
    print(f"Synthetic users: {n_users}")
    print(f"Exercises: {len(EXERCISES)}")
    print(f"Total samples: {len(dataset)}")


if __name__ == "__main__":
    main()
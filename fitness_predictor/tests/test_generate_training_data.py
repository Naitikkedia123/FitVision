from data.exercise_catalog import EXERCISES
from ml.synthetic_dataset import generate_synthetic_dataset


def main():
    dataset = generate_synthetic_dataset(
        exercises=EXERCISES,
        n_users=2000,
    )

    assert len(dataset) == 2000 * len(EXERCISES)

    print("TRAINING DATA GENERATED ✅")
    print(f"Exercises: {len(EXERCISES)}")
    print("Synthetic users: 2000")
    print(f"Rows: {len(dataset)}")

    print("\nFirst row:")
    print(dataset[0])

    print("\nLast row:")
    print(dataset[-1])


if __name__ == "__main__":
    main()
from data.exercise_catalog import EXERCISES
from ml.synthetic_dataset import generate_synthetic_dataset
from ml.training_data_export import save_dataset_to_csv


def main():
    n_users = 10_000

    print("Generating synthetic training dataset...")

    dataset = generate_synthetic_dataset(
        exercises=EXERCISES,
        n_users=n_users,
    )

    print(f"Generated rows: {len(dataset)}")

    expected_rows = n_users * len(EXERCISES)

    assert len(dataset) == expected_rows
    assert len(dataset) == 180_000

    output_path = save_dataset_to_csv(dataset)

    assert output_path.exists()
    assert output_path.is_file()

    print("FULL TRAINING DATASET CREATED ✅")
    print(f"Users: {n_users}")
    print(f"Exercises: {len(EXERCISES)}")
    print(f"Rows: {len(dataset)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
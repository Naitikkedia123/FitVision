from pathlib import Path

from data.exercise_catalog import EXERCISES
from ml.synthetic_dataset import generate_synthetic_dataset
from ml.training_data_export import save_dataset_to_csv


def main():
    dataset = generate_synthetic_dataset(
        exercises=EXERCISES,
        n_users=10,
    )

    output_path = (
        Path("data")
        / "training"
        / "test_synthetic_training_data.csv"
    )

    saved_path = save_dataset_to_csv(
        dataset=dataset,
        output_path=output_path,
    )

    assert saved_path.exists()
    assert saved_path.is_file()

    print("TRAINING DATA EXPORT TEST PASSED ✅")
    print(f"Rows exported: {len(dataset)}")
    print(f"Saved to: {saved_path}")


if __name__ == "__main__":
    main()
from pathlib import Path
import csv
from typing import Any


DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "training"
    / "synthetic_training_data.csv"
)


def save_dataset_to_csv(
    dataset: list[dict[str, Any]],
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
) -> Path:
    if not isinstance(dataset, list):
        raise TypeError("dataset must be a list.")

    if not dataset:
        raise ValueError("dataset cannot be empty.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(dataset[0].keys())

    for row in dataset:
        if set(row.keys()) != set(fieldnames):
            raise ValueError(
                "All dataset rows must contain the same fields."
            )

    with path.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(dataset)

    return path
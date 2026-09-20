from pathlib import Path

from huggingface_hub import hf_hub_download


REPO_ID = "CoderNaitik/FitVision-models"

MODELS_DIR = Path(__file__).resolve().parent / "models"

MODEL_FILES = (
    "duration_model.joblib",
    "reps_model.joblib",
    "sets_model.joblib",
)


def ensure_models_available() -> None:
    """
    Make sure all FitVision prediction models exist locally.

    If a model is already present, nothing is downloaded.
    If it is missing, download it from Hugging Face.
    """

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for filename in MODEL_FILES:
        destination = MODELS_DIR / filename

        if destination.exists() and destination.stat().st_size > 0:
            continue

        hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            local_dir=str(MODELS_DIR),
        )

        if not destination.exists():
            raise FileNotFoundError(
                f"Model download failed: {filename}"
            )
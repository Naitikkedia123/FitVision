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
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for filename in MODEL_FILES:
        destination = MODELS_DIR / filename

        if destination.exists() and destination.stat().st_size > 0:
            print(f"[MODEL] Already exists: {filename}")
            continue

        print(f"[MODEL] START DOWNLOAD: {filename}", flush=True)

        downloaded_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            local_dir=str(MODELS_DIR),
        )

        print(
            f"[MODEL] DOWNLOAD COMPLETE: {filename} -> {downloaded_path}",
            flush=True,
        )

        if not destination.exists():
            raise FileNotFoundError(
                f"Model download failed: {filename}"
            )

        print(
            f"[MODEL] VERIFIED: {filename} "
            f"({destination.stat().st_size / (1024**2):.1f} MB)",
            flush=True,
        )

    print("[MODEL] ALL MODELS AVAILABLE", flush=True)
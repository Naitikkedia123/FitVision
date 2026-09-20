from pathlib import Path

from huggingface_hub import hf_hub_download


REPO_ID = "CoderNaitik/FitVision-models"

MODELS_DIR = Path(__file__).resolve().parent / "models"


def ensure_model_available(filename: str) -> Path:
    destination = MODELS_DIR / filename

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if destination.exists() and destination.stat().st_size > 0:
        print(
            f"[MODEL] Already available: {filename}",
            flush=True,
        )
        return destination

    print(
        f"[MODEL] START DOWNLOAD: {filename}",
        flush=True,
    )

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
        f"({destination.stat().st_size / (1024 ** 2):.1f} MB)",
        flush=True,
    )

    return destination
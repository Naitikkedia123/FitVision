from typing import Any

from ml.ml_predictor import MLDosagePredictor
from rules.dosage_validator import (
    ValidatedDosage,
    validate_predictions,
)
from models.user_profile import UserProfile


class Week1DosageService:
    def __init__(self, predictor=None):
        print(
            "[DOSAGE] Constructor START",
            flush=True,
        )

        if predictor is None:
            print(
                "[DOSAGE] Creating MLDosagePredictor",
                flush=True,
            )

            self.predictor = MLDosagePredictor()

            print(
                "[DOSAGE] MLDosagePredictor CREATED",
                flush=True,
            )

        else:
            self.predictor = predictor

            print(
                "[DOSAGE] Existing predictor supplied",
                flush=True,
            )

        print(
            "[DOSAGE] Constructor END",
            flush=True,
        )

    def generate(
        self,
        user: UserProfile,
        exercises: list[dict[str, Any]],
    ) -> list[ValidatedDosage]:

        print(
            f"[DOSAGE] GENERATE START - "
            f"{len(exercises)} exercises",
            flush=True,
        )

        if not isinstance(user, UserProfile):
            raise TypeError(
                "user must be a UserProfile."
            )

        if not isinstance(exercises, list):
            raise TypeError(
                "exercises must be a list."
            )

        if not exercises:
            print(
                "[DOSAGE] No exercises supplied",
                flush=True,
            )

            return []

        print(
            "[DOSAGE] Starting memory-efficient "
            "batch prediction",
            flush=True,
        )

        predictions = self.predictor.predict_batch(
            user=user,
            exercises=exercises,
        )

        print(
            "[DOSAGE] BATCH PREDICTION COMPLETE",
            flush=True,
        )

        print(
            "[DOSAGE] VALIDATING PREDICTIONS",
            flush=True,
        )

        result = validate_predictions(
            predictions
        )

        print(
            "[DOSAGE] GENERATE COMPLETE",
            flush=True,
        )

        return result
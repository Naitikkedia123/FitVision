from typing import Any
import streamlit as st
from ml.ml_predictor import MLDosagePredictor
from rules.dosage_validator import ValidatedDosage, validate_predictions
from models.user_profile import UserProfile
from model_downloader import ensure_models_available

class Week1DosageService:
    def __init__(self, predictor=None):
        print("[DOSAGE] Constructor START", flush=True)

        if predictor is None:
            print("[DOSAGE] Calling ensure_models_available()", flush=True)
            ensure_models_available()
            print("[DOSAGE] Models available", flush=True)

            print("[DOSAGE] Creating MLDosagePredictor", flush=True)
            self.predictor = MLDosagePredictor()
            print("[DOSAGE] MLDosagePredictor CREATED", flush=True)
        else:
            self.predictor = predictor
            print("[DOSAGE] Existing predictor supplied", flush=True)

        print("[DOSAGE] Constructor END", flush=True)

    def generate(
        self,
        user: UserProfile,
        exercises: list[dict[str, Any]],
    ) -> list[ValidatedDosage]:
        if not isinstance(user, UserProfile):
            raise TypeError("user must be a UserProfile.")

        if not isinstance(exercises, list):
            raise TypeError("exercises must be a list.")



        predictions = [
            self.predictor.predict(user, exercise)
            for exercise in exercises
        ]

        return validate_predictions(predictions)
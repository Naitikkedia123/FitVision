from typing import Any
import streamlit as st
from ml.ml_predictor import MLDosagePredictor
from rules.dosage_validator import ValidatedDosage, validate_predictions
from models.user_profile import UserProfile
from model_downloader import ensure_models_available

class Week1DosageService:
    def __init__(self, predictor=None):
        if predictor is None:
            ensure_models_available()
            self.predictor = MLDosagePredictor()
        else:
            self.predictor = predictor

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
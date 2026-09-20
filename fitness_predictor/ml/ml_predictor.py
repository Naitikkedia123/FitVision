from pathlib import Path
from typing import Any

import joblib

from ml.prediction import DosagePrediction, Week1DosagePredictor
from models.user_profile import UserProfile


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SETS_MODEL_PATH = (
    PROJECT_ROOT / "models" / "sets_model.joblib"
)

REPS_MODEL_PATH = (
    PROJECT_ROOT / "models" / "reps_model.joblib"
)

DURATION_MODEL_PATH = (
    PROJECT_ROOT / "models" / "duration_model.joblib"
)


class MLDosagePredictor(Week1DosagePredictor):
    """
    Production dosage predictor using the trained ML models.

    The predictor produces raw continuous predictions.
    DosageValidator remains responsible for enforcing the
    final dosage constraints.
    """

    def __init__(
        self,
        sets_model_path: str | Path = SETS_MODEL_PATH,
        reps_model_path: str | Path = REPS_MODEL_PATH,
        duration_model_path: str | Path = DURATION_MODEL_PATH,
    ):
        self.sets_model_path = Path(sets_model_path)
        self.reps_model_path = Path(reps_model_path)
        self.duration_model_path = Path(duration_model_path)

        self.sets_bundle: dict[str, Any] | None = None
        self.reps_bundle: dict[str, Any] | None = None
        self.duration_bundle: dict[str, Any] | None = None

    @staticmethod
    def _load_model(
        model_path: str | Path,
        model_name: str,
    ) -> dict[str, Any]:
        path = Path(model_path)

        if not path.exists():
            raise FileNotFoundError(
                f"{model_name} model not found: {path}"
            )

        bundle = joblib.load(path)

        required_keys = {
            "model",
            "preprocessor",
            "feature_columns",
        }

        missing_keys = required_keys - set(bundle.keys())

        if missing_keys:
            raise ValueError(
                f"{model_name} model is missing keys: "
                f"{sorted(missing_keys)}"
            )

        return bundle

    @staticmethod
    def _build_features(
        user: UserProfile,
        exercise: dict[str, Any],
    ) -> dict[str, Any]:
        if not user.user_id:
            # user_id is not an ML feature, but this helps catch
            # accidentally incomplete production profiles.
            pass

        height_m = user.height_cm / 100.0
        bmi = user.weight_kg / (height_m ** 2)

        return {
            "age": user.age,
            "height_cm": user.height_cm,
            "weight_kg": user.weight_kg,
            "bmi": bmi,
            "fitness_level": user.fitness_level,
            "activity_level": user.activity_level,
            "workout_time_min": user.workout_time_min,
            "difficulty": exercise["difficulty"],
            "impact_level": exercise["impact_level"],
            "knee_flexion_level": exercise[
                "knee_flexion_level"
            ],
            "hip_load_level": exercise["hip_load_level"],
            "shoulder_overhead_required": int(
                exercise["shoulder_overhead_required"]
            ),
            "wrist_weight_bearing": int(
                exercise["wrist_weight_bearing"]
            ),
            "back_load_level": exercise["back_load_level"],
            "ankle_load_level": exercise["ankle_load_level"],
            "floor_required": int(
                exercise["floor_required"]
            ),
            "single_leg": int(
                exercise["single_leg"]
            ),
            "goal": user.goal,
            "exercise_id": exercise["id"],
            "measurement_type": exercise["measurement_type"],
        }

    @staticmethod
    def _predict(
        bundle: dict[str, Any],
        features: dict[str, Any],
    ) -> float:
        import pandas as pd

        dataframe = pd.DataFrame([features])

        feature_columns = bundle["feature_columns"]

        dataframe = dataframe[feature_columns]

        encoded = bundle["preprocessor"].transform(
            dataframe
        )

        prediction = bundle["model"].predict(encoded)

        if len(prediction) != 1:
            raise RuntimeError(
                "ML model returned an unexpected number "
                "of predictions."
            )

        return float(prediction[0])


    def predict(
        self,
        user: UserProfile,
        exercise: dict[str, Any],
    ) -> DosagePrediction:
        if not isinstance(user, UserProfile):
            raise TypeError("user must be a UserProfile.")

        if not isinstance(exercise, dict):
            raise TypeError("exercise must be a dictionary.")

        exercise_id = exercise.get("id")

        if not exercise_id:
            raise ValueError(
                "Exercise is missing its id."
            )

        measurement_type = exercise.get(
            "measurement_type"
        )

        if measurement_type not in {"reps", "time"}:
            raise ValueError(
                f"Unsupported measurement_type: "
                f"{measurement_type!r}"
            )

        features = self._build_features(
            user=user,
            exercise=exercise,
        )

        # Load the sets model only when it is actually needed.
        if self.sets_bundle is None:
            self.sets_bundle = self._load_model(
                self.sets_model_path,
                "sets",
            )

        sets_prediction = self._predict(
            bundle=self.sets_bundle,
            features=features,
        )

        if measurement_type == "reps":
            # Load the reps model only for repetition-based exercises.
            if self.reps_bundle is None:
                self.reps_bundle = self._load_model(
                    self.reps_model_path,
                    "reps",
                )

            reps_prediction = self._predict(
                bundle=self.reps_bundle,
                features=features,
            )

            return DosagePrediction(
                exercise_id=exercise_id,
                sets=sets_prediction,
                reps=reps_prediction,
                duration_seconds=None,
            )

        # Load the duration model only for time-based exercises.
        if self.duration_bundle is None:
            self.duration_bundle = self._load_model(
                self.duration_model_path,
                "duration",
            )

        duration_prediction = self._predict(
            bundle=self.duration_bundle,
            features=features,
        )

        return DosagePrediction(
            exercise_id=exercise_id,
            sets=sets_prediction,
            reps=None,
            duration_seconds=duration_prediction,
        )

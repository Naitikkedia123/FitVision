from pathlib import Path
from typing import Any
import os
import psutil

import joblib

from ml.prediction import DosagePrediction, Week1DosagePredictor
from models.user_profile import UserProfile
from model_downloader import ensure_model_available


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

    Models are downloaded from Hugging Face only when they
    are actually needed.

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

        # Models are loaded lazily.
        # They remain None until they are actually required.
        self.sets_bundle: dict[str, Any] | None = None
        self.reps_bundle: dict[str, Any] | None = None
        self.duration_bundle: dict[str, Any] | None = None

        print(
            "[ML] MLDosagePredictor initialized",
            flush=True,
        )

    @staticmethod
    def _load_model(
        model_path: str | Path,
        model_name: str,
    ) -> dict[str, Any]:
        """
        Download the requested model if necessary and load it.

        IMPORTANT:
        The model must be downloaded BEFORE checking whether
        the local file exists.
        """

        path = Path(model_path)

        print(
            f"[ML] _load_model START: {model_name}",
            flush=True,
        )

        print(
            f"[ML] Model path: {path}",
            flush=True,
        )

        # ---------------------------------------------------------
        # ENSURE MODEL EXISTS
        # ---------------------------------------------------------
        print(
            f"[ML] Ensuring model is available: {model_name}",
            flush=True,
        )

        ensure_model_available(path.name)

        # ---------------------------------------------------------
        # VERIFY LOCAL FILE
        # ---------------------------------------------------------
        if not path.exists():
            print(
                f"[ML] Model still NOT FOUND after download: {path}",
                flush=True,
            )

            raise FileNotFoundError(
                f"{model_name} model not found: {path}"
            )

        file_size_mb = path.stat().st_size / (1024 ** 2)

        print(f"[ML] Model exists: {file_size_mb:.1f} MB", flush=True)

        process = psutil.Process(os.getpid())
        memory = process.memory_info()

        print(
            f"[ML] RAM BEFORE LOAD: "
            f"{memory.rss / (1024 ** 3):.2f} GB",
            flush=True,
        )

        print(f"[ML] joblib.load START: {model_name}", flush=True)

        bundle = joblib.load(path, mmap_mode="r")

        print(f"[ML] joblib.load COMPLETE: {model_name}", flush=True)

        # ---------------------------------------------------------
        # VERIFY MODEL BUNDLE
        # ---------------------------------------------------------
        required_keys = {
            "model",
            "preprocessor",
            "feature_columns",
        }

        missing_keys = required_keys - set(bundle.keys())

        if missing_keys:
            print(
                f"[ML] Missing keys in {model_name}: "
                f"{sorted(missing_keys)}",
                flush=True,
            )

            raise ValueError(
                f"{model_name} model is missing keys: "
                f"{sorted(missing_keys)}"
            )

        print(
            f"[ML] Model bundle verified: {model_name}",
            flush=True,
        )

        return bundle

    @staticmethod
    def _build_features(
        user: UserProfile,
        exercise: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build the feature dictionary expected by the ML models.
        """

        if not user.user_id:
            # user_id is not an ML feature, but this helps catch
            # accidentally incomplete production profiles.
            pass

        height_m = user.height_cm / 100.0
        bmi = user.weight_kg / (height_m ** 2)

        features = {
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

        print(
            f"[ML] Features built for: {exercise.get('id')}",
            flush=True,
        )

        return features

    @staticmethod
    def _predict(
        bundle: dict[str, Any],
        features: dict[str, Any],
    ) -> float:
        """
        Run preprocessing and prediction using a loaded model bundle.
        """

        import pandas as pd

        print(
            "[ML] _predict START",
            flush=True,
        )

        dataframe = pd.DataFrame([features])

        feature_columns = bundle["feature_columns"]

        print(
            f"[ML] Feature columns: {len(feature_columns)}",
            flush=True,
        )

        dataframe = dataframe[feature_columns]

        print(
            "[ML] Preprocessor transform START",
            flush=True,
        )

        encoded = bundle["preprocessor"].transform(
            dataframe
        )

        print(
            "[ML] Preprocessor transform COMPLETE",
            flush=True,
        )

        print(
            "[ML] Model predict START",
            flush=True,
        )

        prediction = bundle["model"].predict(encoded)

        print(
            "[ML] Model predict COMPLETE",
            flush=True,
        )

        if len(prediction) != 1:
            raise RuntimeError(
                "ML model returned an unexpected number "
                "of predictions."
            )

        result = float(prediction[0])

        print(
            f"[ML] Prediction result: {result}",
            flush=True,
        )

        return result

    def predict(
        self,
        user: UserProfile,
        exercise: dict[str, Any],
    ) -> DosagePrediction:
        """
        Predict dosage for a single exercise.
        """

        exercise_id = exercise.get("id")

        print(
            "========================================",
            flush=True,
        )

        print(
            f"[ML] PREDICT START: {exercise_id}",
            flush=True,
        )

        # ---------------------------------------------------------
        # VALIDATION
        # ---------------------------------------------------------
        if not isinstance(user, UserProfile):
            raise TypeError(
                "user must be a UserProfile."
            )

        if not isinstance(exercise, dict):
            raise TypeError(
                "exercise must be a dictionary."
            )

        if not exercise_id:
            raise ValueError(
                "Exercise is missing its id."
            )

        measurement_type = exercise.get(
            "measurement_type"
        )

        print(
            f"[ML] Measurement type: {measurement_type}",
            flush=True,
        )

        if measurement_type not in {"reps", "time"}:
            raise ValueError(
                f"Unsupported measurement_type: "
                f"{measurement_type!r}"
            )

        # ---------------------------------------------------------
        # BUILD FEATURES
        # ---------------------------------------------------------
        print(
            "[ML] Building features",
            flush=True,
        )

        features = self._build_features(
            user=user,
            exercise=exercise,
        )

        print(
            "[ML] Features ready",
            flush=True,
        )

        # ---------------------------------------------------------
        # SETS MODEL
        # ---------------------------------------------------------
        if self.sets_bundle is None:
            print(
                "[ML] Loading SETS model",
                flush=True,
            )

            self.sets_bundle = self._load_model(
                self.sets_model_path,
                "sets",
            )

            print(
                "[ML] SETS model loaded and retained",
                flush=True,
            )
        else:
            print(
                "[ML] SETS model already loaded",
                flush=True,
            )

        print(
            "[ML] Predicting SETS",
            flush=True,
        )

        sets_prediction = self._predict(
            bundle=self.sets_bundle,
            features=features,
        )

        print(
            f"[ML] SETS prediction complete: "
            f"{sets_prediction}",
            flush=True,
        )

        # ---------------------------------------------------------
        # REP-BASED EXERCISES
        # ---------------------------------------------------------
        if measurement_type == "reps":

            if self.reps_bundle is None:
                print(
                    "[ML] Loading REPS model",
                    flush=True,
                )

                self.reps_bundle = self._load_model(
                    self.reps_model_path,
                    "reps",
                )

                print(
                    "[ML] REPS model loaded and retained",
                    flush=True,
                )
            else:
                print(
                    "[ML] REPS model already loaded",
                    flush=True,
                )

            print(
                "[ML] Predicting REPS",
                flush=True,
            )

            reps_prediction = self._predict(
                bundle=self.reps_bundle,
                features=features,
            )

            print(
                f"[ML] REPS prediction complete: "
                f"{reps_prediction}",
                flush=True,
            )

            print(
                f"[ML] PREDICT COMPLETE: {exercise_id}",
                flush=True,
            )

            return DosagePrediction(
                exercise_id=exercise_id,
                sets=sets_prediction,
                reps=reps_prediction,
                duration_seconds=None,
            )

        # ---------------------------------------------------------
        # TIME-BASED EXERCISES
        # ---------------------------------------------------------
        print(
            "[ML] Time-based exercise detected",
            flush=True,
        )

        if self.duration_bundle is None:
            print(
                "[ML] Loading DURATION model",
                flush=True,
            )

            self.duration_bundle = self._load_model(
                self.duration_model_path,
                "duration",
            )

            print(
                "[ML] DURATION model loaded and retained",
                flush=True,
            )
        else:
            print(
                "[ML] DURATION model already loaded",
                flush=True,
            )

        print(
            "[ML] Predicting DURATION",
            flush=True,
        )

        duration_prediction = self._predict(
            bundle=self.duration_bundle,
            features=features,
        )

        print(
            f"[ML] DURATION prediction complete: "
            f"{duration_prediction}",
            flush=True,
        )

        print(
            f"[ML] PREDICT COMPLETE: {exercise_id}",
            flush=True,
        )

        return DosagePrediction(
            exercise_id=exercise_id,
            sets=sets_prediction,
            reps=None,
            duration_seconds=duration_prediction,
        )
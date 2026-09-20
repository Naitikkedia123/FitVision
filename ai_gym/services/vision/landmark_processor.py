from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

from ai_gym.detectors.squat import SquatDetector
from ai_gym.detectors.pushup import PushUpDetector
from ai_gym.detectors.biceps_curl import BicepsCurlDetector
from ai_gym.detectors.shoulder_press import ShoulderPressDetector
from ai_gym.detectors.lunges import LungesDetector
from ai_gym.detectors.calf_raise import CalfRaiseDetector
from ai_gym.detectors.march_in_place import MarchInPlaceDetector
from ai_gym.detectors.standing_knee_raise import StandingKneeRaiseDetector
from ai_gym.detectors.low_impact_jumping_jack import LowImpactJumpingJackDetector
from ai_gym.detectors.wall_sit import WallSitDetector
from ai_gym.detectors.standing_side_leg_raise import StandingSideLegRaiseDetector
from ai_gym.detectors.hamstring_curl import HamstringCurlDetector
from ai_gym.detectors.hip_extension import HipExtensionDetector
from ai_gym.detectors.glute_bridge import GluteBridgeDetector
from ai_gym.detectors.sit_to_stand import SitToStandDetector
from ai_gym.detectors.wall_push_up import WallPushUpDetector
from ai_gym.detectors.knee_push_up import KneePushUpDetector
from ai_gym.detectors.plank import PlankDetector

try:
    from shared.exercise_mapping import (
        EXERCISE_EXECUTION_MAP,
        get_trainer_exercise_type,
        is_trainer_supported,
    )
except ModuleNotFoundError:
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[3]

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from shared.exercise_mapping import (
        EXERCISE_EXECUTION_MAP,
        get_trainer_exercise_type,
        is_trainer_supported,
    )


@dataclass
class Landmark:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    visibility: float = 0.0
    presence: float = 0.0

    
class LandmarkProcessor:
    """
    Backend-only exercise processor.

    The browser sends pose landmarks; this class never receives
    or processes camera frames.
    """

    _DETECTOR_FACTORIES: dict[str, Callable] = {
        "Squats": SquatDetector,
        "Push-ups": PushUpDetector,
        "Biceps Curls (Dumbbell)": BicepsCurlDetector,
        "Shoulder Press": ShoulderPressDetector,
        "Lunges": LungesDetector,
        "Calf Raises": CalfRaiseDetector,
        "March in Place": MarchInPlaceDetector,
        "Standing Knee Raises": StandingKneeRaiseDetector,
        "Low-Impact Jumping Jacks": LowImpactJumpingJackDetector,
        "Wall Sits": WallSitDetector,
        "Standing Side Leg Raises": StandingSideLegRaiseDetector,
        "Standing Hamstring Curls": HamstringCurlDetector,
        "Standing Hip Extensions": HipExtensionDetector,
        "Glute Bridges": GluteBridgeDetector,
        "Sit-to-Stands": SitToStandDetector,
        "Wall Push-Ups": WallPushUpDetector,
        "Knee Push-Ups": KneePushUpDetector,
        "Planks": PlankDetector,
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"

        # One persistent detector instance per exercise.
        # Detectors are stateful because rep counting depends
        # on previous frames.
        self._detectors = {
            exercise_type: factory()
            for exercise_type, factory in self._DETECTOR_FACTORIES.items()
        }

    def set_exercise(self, exercise_type: str) -> None:
        if not isinstance(exercise_type, str):
            raise TypeError("exercise_type must be a string.")

        exercise_type = exercise_type.strip()

        if not exercise_type:
            raise ValueError("exercise_type cannot be empty.")

        if exercise_type in EXERCISE_EXECUTION_MAP:
            if not is_trainer_supported(exercise_type):
                raise ValueError(
                    f"Exercise '{exercise_type}' does not yet have "
                    "an AI GYM execution implementation."
                )

            trainer_exercise_type = get_trainer_exercise_type(
                exercise_type
            )

        elif exercise_type in self._detectors:
            trainer_exercise_type = exercise_type

        else:
            raise ValueError(
                f"Unsupported exercise: {exercise_type}"
            )

        if trainer_exercise_type not in self._detectors:
            raise ValueError(
                f"No detector registered for "
                f"'{trainer_exercise_type}'."
            )

        with self._lock:
            self._exercise_type = trainer_exercise_type

    def reset_current_exercise(self) -> None:
        """
        Reset the currently selected detector.

        This is called only when a new exercise/workout is
        actually configured. It must NOT be called on every
        0.25-second metrics update because detector state is
        required for rep counting.
        """

        with self._lock:
            detector = self._detectors.get(
                self._exercise_type
            )

            if detector is None:
                raise ValueError(
                    f"No detector registered for "
                    f"'{self._exercise_type}'."
                )

            reset_method = getattr(
                detector,
                "reset",
                None,
            )

            if callable(reset_method):
                reset_method()

            else:
                # Future-proof fallback:
                # if a newly added detector does not yet expose
                # reset(), create a fresh detector instance.
                factory = self._DETECTOR_FACTORIES.get(
                    self._exercise_type
                )

                if factory is None:
                    raise ValueError(
                        f"No detector factory registered for "
                        f"'{self._exercise_type}'."
                    )

                self._detectors[
                    self._exercise_type
                ] = factory()

            # The UI should not display metrics from the
            # previous exercise.
            self._latest_metrics = None

    def get_exercise(self) -> str:
        with self._lock:
            return self._exercise_type

    def set_latest_metrics(self, metrics: dict) -> None:
        with self._lock:
            self._latest_metrics = dict(metrics)

    def get_latest_metrics(self):
        with self._lock:
            if self._latest_metrics is None:
                return None

            return dict(self._latest_metrics)

    @staticmethod
    def _convert_landmarks(
        landmarks_data: list[dict],
    ):
        converted = []

        for item in landmarks_data:
            converted.append(
                Landmark(
                    x=float(item.get("x", 0.0)),
                    y=float(item.get("y", 0.0)),
                    z=float(item.get("z", 0.0)),
                    visibility=float(
                        item.get("visibility", 0.0)
                    ),
                    presence=float(
                        item.get("presence", 0.0)
                    ),
                )
            )

        return converted

    def process_landmarks(
        self,
        landmarks_data: list[dict] | None,
    ) -> dict:

        if not landmarks_data:
            metrics = {
                "pose_detected": False
            }

            self.set_latest_metrics(metrics)

            return metrics

        landmarks = self._convert_landmarks(
            landmarks_data
        )

        exercise_type = self.get_exercise()

        detector = self._detectors.get(
            exercise_type
        )

        if detector is None:
            raise ValueError(
                f"No detector registered for "
                f"'{exercise_type}'."
            )

        metrics = detector.process(
            landmarks
        )

        metrics["pose_detected"] = True

        self.set_latest_metrics(
            metrics
        )

        return metrics

    def process_landmark_batch(
        self,
        landmark_frames,
    ):

        latest_metrics = None

        if not landmark_frames:
            return self.process_landmarks(
                None
            )

        for frame in landmark_frames:

            landmarks = frame.get(
                "landmarks"
            )

            if landmarks:
                latest_metrics = (
                    self.process_landmarks(
                        landmarks
                    )
                )

            else:
                latest_metrics = (
                    self.process_landmarks(
                        None
                    )
                )

        return latest_metrics
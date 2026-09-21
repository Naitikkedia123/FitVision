from ai_gym.core.base_exercise import BaseExercise
import time
import math


class HipExtensionDetector(BaseExercise):
    """Counts standing hip extensions from change in normalized ankle displacement."""

    MIN_VISIBILITY = 0.45
    EXTEND_THRESHOLD = 0.07
    RELEASE_THRESHOLD = 0.025
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "neutral"
        self.reps = 0
        self.active_side = None
        self._baseline_left = None
        self._baseline_right = None
        self._last_rep_time = 0.0

    def _normalized_extension(self, landmarks, hip_idx, ankle_idx):
        leg_length = math.hypot(
            landmarks[ankle_idx].x - landmarks[hip_idx].x,
            landmarks[ankle_idx].y - landmarks[hip_idx].y,
        )
        return abs(landmarks[ankle_idx].x - landmarks[hip_idx].x) / max(leg_length, 1e-6)

    def process(self, landmarks):
        required = [23, 24, 27, 28]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if max(getattr(landmarks[i], "visibility", 1.0) for i in required) < self.MIN_VISIBILITY:
            return {"reps": self.reps, "stage": self.stage, "status": "Legs not clearly visible"}

        left = self._normalized_extension(landmarks, 23, 27)
        right = self._normalized_extension(landmarks, 24, 28)

        # Establish a per-user neutral baseline so camera angle and body shape
        # do not make the detector think the leg is already extended.
        if self._baseline_left is None:
            self._baseline_left = left
        else:
            self._baseline_left = min(self._baseline_left, left)
        if self._baseline_right is None:
            self._baseline_right = right
        else:
            self._baseline_right = min(self._baseline_right, right)

        left_change = max(0.0, left - self._baseline_left)
        right_change = max(0.0, right - self._baseline_right)
        change = max(left_change, right_change)
        side = "left" if left_change >= right_change else "right"

        if self.stage == "neutral" and change >= self.EXTEND_THRESHOLD:
            self.stage = "extended"
            self.active_side = side
        elif self.stage == "extended":
            current = left_change if self.active_side == "left" else right_change
            if current <= self.RELEASE_THRESHOLD:
                now = time.monotonic()
                if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                    self.reps += 1
                    self._last_rep_time = now
                self.stage = "neutral"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "extension": round(change, 3),
            "side": self.active_side,
            "status": "Extend one leg back" if self.stage == "neutral" else "Return to neutral",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "neutral"
        self.reps = 0
        self.active_side = None
        self._baseline_left = None
        self._baseline_right = None
        self._last_rep_time = 0.0

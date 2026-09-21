import time

from ai_gym.core.base_exercise import BaseExercise


class MarchInPlaceDetector(BaseExercise):
    """Tracks practical marching from alternating knee lift."""

    KNEE_RAISE_THRESHOLD = 0.03
    KNEE_RELEASE_THRESHOLD = 0.018
    STEP_COOLDOWN_SECONDS = 0.18
    MARCH_TIMEOUT_SECONDS = 1.50

    def __init__(self):
        super().__init__(measurement_type="time")
        self.stage = "not_marching"
        self.duration_seconds = 0.0
        self._start_time = None
        self._accumulated_duration = 0.0
        self._last_valid_time = None
        self._last_step_time = 0.0
        self._left_up = False
        self._right_up = False

    def process(self, landmarks):
        required = [23, 24, 25, 26]
        now = time.monotonic()
        if landmarks is None or len(landmarks) <= max(required):
            self._handle_missing_frame(now)
            return {"duration_seconds": round(self.duration_seconds, 2), "stage": self.stage, "status": "Landmarks unavailable"}

        if any(getattr(landmarks[i], "visibility", 1.0) < 0.45 for i in required):
            self._handle_missing_frame(now)
            return {"duration_seconds": round(self.duration_seconds, 2), "stage": self.stage, "status": "Legs not clearly visible"}

        hip_y = (landmarks[23].y + landmarks[24].y) / 2
        left_lift = hip_y - landmarks[25].y
        right_lift = hip_y - landmarks[26].y
        left_high = left_lift >= self.KNEE_RAISE_THRESHOLD
        right_high = right_lift >= self.KNEE_RAISE_THRESHOLD
        left_low = left_lift <= self.KNEE_RELEASE_THRESHOLD
        right_low = right_lift <= self.KNEE_RELEASE_THRESHOLD

        if left_high and not self._left_up:
            self._left_up = True
            self._start_march(now)
        elif left_low:
            self._left_up = False

        if right_high and not self._right_up:
            self._right_up = True
            self._start_march(now)
        elif right_low:
            self._right_up = False

        if self._start_time is not None:
            self._last_valid_time = now
            self.duration_seconds = self._accumulated_duration + (now - self._start_time)
            self.stage = "marching"
        elif self._last_valid_time is not None and now - self._last_valid_time <= self.MARCH_TIMEOUT_SECONDS:
            self.stage = "marching"
        else:
            self.stage = "not_marching"

        return {
            "duration_seconds": round(self.duration_seconds, 2),
            "stage": self.stage,
            "left_knee_lift": round(left_lift, 3),
            "right_knee_lift": round(right_lift, 3),
            "status": "Keep marching" if self.stage == "marching" else "Lift either knee to start",
        }

    def _start_march(self, now):
        if self._start_time is None:
            self._start_time = now
            self._last_valid_time = now
            self.stage = "marching"

    def _handle_missing_frame(self, now):
        if self._start_time is None:
            return
        if self._last_valid_time is not None and now - self._last_valid_time <= self.MARCH_TIMEOUT_SECONDS:
            self.duration_seconds = self._accumulated_duration + (now - self._start_time)
            return
        self._pause(now)

    def _pause(self, now):
        if self._start_time is not None:
            self._accumulated_duration += now - self._start_time
        self._start_time = None
        self.duration_seconds = self._accumulated_duration
        self.stage = "not_marching"
        self._last_valid_time = None

    def reset(self):
        self.reset_common_state()
        self.stage = "not_marching"
        self.duration_seconds = 0.0
        self._start_time = None
        self._accumulated_duration = 0.0
        self._last_valid_time = None
        self._last_step_time = 0.0
        self._left_up = False
        self._right_up = False

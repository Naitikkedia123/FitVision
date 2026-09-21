import time

from ai_gym.core.base_exercise import BaseExercise


class WallSitDetector(BaseExercise):
    """Tracks cumulative wall-sit time with a broad knee-angle range."""

    START_MIN_ANGLE = 65.0
    START_MAX_ANGLE = 135.0
    RELEASE_MIN_ANGLE = 60.0
    RELEASE_MAX_ANGLE = 140.0
    TIMEOUT_SECONDS = 1.50

    def __init__(self):
        super().__init__(measurement_type="time")
        self.stage = "not_holding"
        self.duration_seconds = 0.0
        self._start_time = None
        self._accumulated_duration = 0.0
        self._last_valid_time = None
        self._holding = False

    def process(self, landmarks):
        required = [23, 25, 27]
        now = time.monotonic()
        if landmarks is None or len(landmarks) <= max(required):
            self._handle_missing_frame(now)
            return {"duration_seconds": round(self.duration_seconds, 2), "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < 0.45 for i in required):
            self._handle_missing_frame(now)
            return {"duration_seconds": round(self.duration_seconds, 2), "stage": self.stage, "status": "Legs not clearly visible"}

        knee_angle = self.calculate_angle(self.get_point(landmarks, 23), self.get_point(landmarks, 25), self.get_point(landmarks, 27))

        if not self._holding:
            valid = self.START_MIN_ANGLE <= knee_angle <= self.START_MAX_ANGLE
            if valid:
                self._holding = True
                self._start_time = now if self._start_time is None else self._start_time
                self._last_valid_time = now
                self.stage = "holding"
        else:
            valid = self.RELEASE_MIN_ANGLE <= knee_angle <= self.RELEASE_MAX_ANGLE
            if valid:
                self._last_valid_time = now
                self.stage = "holding"
            elif self._last_valid_time is not None and now - self._last_valid_time > self.TIMEOUT_SECONDS:
                self._pause(now)

        self.duration_seconds = self._accumulated_duration + (now - self._start_time) if self._start_time is not None else self._accumulated_duration
        return {
            "duration_seconds": round(self.duration_seconds, 2),
            "knee_angle": round(knee_angle, 2),
            "stage": self.stage,
            "status": "Hold the wall sit" if self.stage == "holding" else "Bend your knees and hold",
        }

    def _handle_missing_frame(self, now):
        if self._start_time is None:
            return
        if self._last_valid_time is not None and now - self._last_valid_time <= self.TIMEOUT_SECONDS:
            self.duration_seconds = self._accumulated_duration + (now - self._start_time)
            return
        self._pause(now)

    def _pause(self, now):
        if self._start_time is not None:
            self._accumulated_duration += now - self._start_time
        self._start_time = None
        self.duration_seconds = self._accumulated_duration
        self.stage = "not_holding"
        self._holding = False
        self._last_valid_time = None

    def reset(self):
        self.reset_common_state()
        self.stage = "not_holding"
        self.duration_seconds = 0.0
        self._start_time = None
        self._accumulated_duration = 0.0
        self._last_valid_time = None
        self._holding = False

import time

from ai_gym.core.base_exercise import BaseExercise


class PlankDetector(BaseExercise):
    """Tracks a practical plank hold with relaxed straightness limits."""

    START_BODY_ANGLE = 135.0
    START_KNEE_ANGLE = 135.0
    RELEASE_BODY_ANGLE = 130.0
    RELEASE_KNEE_ANGLE = 130.0
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
        required = [11, 23, 25, 27]
        now = time.monotonic()
        if landmarks is None or len(landmarks) <= max(required):
            self._handle_missing_frame(now)
            return {"duration_seconds": round(self.duration_seconds, 2), "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < 0.45 for i in required):
            self._handle_missing_frame(now)
            return {"duration_seconds": round(self.duration_seconds, 2), "stage": self.stage, "status": "Body not clearly visible"}

        shoulder = self.get_point(landmarks, 11)
        hip = self.get_point(landmarks, 23)
        knee = self.get_point(landmarks, 25)
        ankle = self.get_point(landmarks, 27)
        body_angle = self.calculate_angle(shoulder, hip, knee)
        knee_angle = self.calculate_angle(hip, knee, ankle)

        if not self._holding:
            if body_angle >= self.START_BODY_ANGLE and knee_angle >= self.START_KNEE_ANGLE:
                self._holding = True
                self._start_time = now if self._start_time is None else self._start_time
                self._last_valid_time = now
                self.stage = "holding"
        else:
            valid = body_angle >= self.RELEASE_BODY_ANGLE and knee_angle >= self.RELEASE_KNEE_ANGLE
            if valid:
                self._last_valid_time = now
                self.stage = "holding"
            elif self._last_valid_time is not None and now - self._last_valid_time > self.TIMEOUT_SECONDS:
                self._pause(now)

        self.duration_seconds = self._accumulated_duration + (now - self._start_time) if self._start_time is not None else self._accumulated_duration
        return {
            "duration_seconds": round(self.duration_seconds, 2),
            "body_angle": round(body_angle, 2),
            "knee_angle": round(knee_angle, 2),
            "stage": self.stage,
            "status": "Hold your plank" if self.stage == "holding" else "Get into a plank position",
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

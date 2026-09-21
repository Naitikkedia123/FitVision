from ai_gym.core.base_exercise import BaseExercise
import time


class HamstringCurlDetector(BaseExercise):
    """Counts standing hamstring curls with relaxed knee-angle thresholds."""

    MIN_VISIBILITY = 0.45
    CURL_THRESHOLD = 140
    RELEASE_THRESHOLD = 150
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "down"
        self.reps = 0
        self.active_side = None
        self._last_rep_time = 0.0

    def process(self, landmarks):
        required = [23, 24, 25, 26, 27, 28]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if max(getattr(landmarks[i], "visibility", 1.0) for i in required) < self.MIN_VISIBILITY:
            return {"reps": self.reps, "stage": self.stage, "status": "Legs not clearly visible"}

        la = self.calculate_angle(self.get_point(landmarks, 23), self.get_point(landmarks, 25), self.get_point(landmarks, 27))
        ra = self.calculate_angle(self.get_point(landmarks, 24), self.get_point(landmarks, 26), self.get_point(landmarks, 28))

        if self.stage == "down":
            if la <= self.CURL_THRESHOLD and la <= ra:
                self.active_side = "left"
                self.stage = "up"
            elif ra <= self.CURL_THRESHOLD:
                self.active_side = "right"
                self.stage = "up"
        else:
            current = la if self.active_side == "left" else ra
            if current >= self.RELEASE_THRESHOLD:
                now = time.monotonic()
                if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                    self.reps += 1
                    self._last_rep_time = now
                self.stage = "down"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "left_knee_angle": round(la, 1),
            "right_knee_angle": round(ra, 1),
            "side": self.active_side,
            "status": "Curl your heel up" if self.stage == "down" else "Lower your heel",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "down"
        self.reps = 0
        self.active_side = None
        self._last_rep_time = 0.0

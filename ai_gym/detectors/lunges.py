from ai_gym.core.base_exercise import BaseExercise
import time


class LungesDetector(BaseExercise):
    """Counts lunges using the most flexed visible knee."""

    MIN_VISIBILITY = 0.45
    DOWN_THRESHOLD = 120
    UP_THRESHOLD = 145
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "up"
        self.reps = 0
        self._last_rep_time = 0.0

    def process(self, landmarks):
        required = [23, 24, 25, 26, 27, 28]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if max(getattr(landmarks[i], "visibility", 1.0) for i in required) < self.MIN_VISIBILITY:
            return {"reps": self.reps, "stage": self.stage, "status": "Legs not clearly visible"}

        left = self.calculate_angle(self.get_point(landmarks, 23), self.get_point(landmarks, 25), self.get_point(landmarks, 27))
        right = self.calculate_angle(self.get_point(landmarks, 24), self.get_point(landmarks, 26), self.get_point(landmarks, 28))
        front_angle = min(left, right)

        if self.stage == "up" and front_angle <= self.DOWN_THRESHOLD:
            self.stage = "down"
        elif self.stage == "down" and front_angle >= self.UP_THRESHOLD:
            now = time.monotonic()
            if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                self.reps += 1
                self._last_rep_time = now
            self.stage = "up"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "front_knee_angle": round(front_angle, 1),
            "left_knee_angle": round(left, 1),
            "right_knee_angle": round(right, 1),
            "status": "Return to standing" if self.stage == "down" else "Step and bend",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "up"
        self.reps = 0
        self._last_rep_time = 0.0

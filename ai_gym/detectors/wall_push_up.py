from ai_gym.core.base_exercise import BaseExercise
import time


class WallPushUpDetector(BaseExercise):
    """Counts easy-to-perform wall push-ups from the arm angle."""

    MIN_VISIBILITY = 0.45
    DOWN_THRESHOLD = 115
    UP_THRESHOLD = 145
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "up"
        self.reps = 0
        self._last_rep_time = 0.0

    def process(self, landmarks):
        required = [11, 13, 15]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Upper body not clearly visible"}

        shoulder = self.get_point(landmarks, 11)
        elbow = self.get_point(landmarks, 13)
        wrist = self.get_point(landmarks, 15)
        elbow_angle = self.calculate_angle(shoulder, elbow, wrist)

        if self.stage == "up" and elbow_angle <= self.DOWN_THRESHOLD:
            self.stage = "down"
        elif self.stage == "down" and elbow_angle >= self.UP_THRESHOLD:
            now = time.monotonic()
            if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                self.reps += 1
                self._last_rep_time = now
            self.stage = "up"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "elbow_angle": round(elbow_angle, 1),
            "status": "Push away from the wall" if self.stage == "down" else "Lean toward the wall",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "up"
        self.reps = 0
        self._last_rep_time = 0.0

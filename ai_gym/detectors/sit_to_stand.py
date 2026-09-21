from ai_gym.core.base_exercise import BaseExercise
import time


class SitToStandDetector(BaseExercise):
    """Counts sit-to-stand repetitions with relaxed posture requirements."""

    MIN_VISIBILITY = 0.45
    SIT_THRESHOLD = 135
    STAND_THRESHOLD = 145
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "standing"
        self.reps = 0
        self._last_rep_time = 0.0

    def process(self, landmarks):
        required = [11, 23, 25, 27]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Body not clearly visible"}

        hip = self.get_point(landmarks, 23)
        knee = self.get_point(landmarks, 25)
        ankle = self.get_point(landmarks, 27)
        shoulder = self.get_point(landmarks, 11)
        knee_angle = self.calculate_angle(hip, knee, ankle)
        hip_angle = self.calculate_angle(shoulder, hip, knee)

        if self.stage == "standing" and knee_angle <= self.SIT_THRESHOLD:
            self.stage = "sitting"
        elif self.stage == "sitting" and knee_angle >= self.STAND_THRESHOLD:
            now = time.monotonic()
            if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                self.reps += 1
                self._last_rep_time = now
            self.stage = "standing"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "knee_angle": round(knee_angle, 1),
            "hip_angle": round(hip_angle, 1),
            "status": "Stand up" if self.stage == "sitting" else "Sit down",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "standing"
        self.reps = 0
        self._last_rep_time = 0.0

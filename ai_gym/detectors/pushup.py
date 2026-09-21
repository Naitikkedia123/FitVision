from ai_gym.core.base_exercise import BaseExercise
import time


class PushUpDetector(BaseExercise):
    """Counts practical push-ups from elbow flexion."""

    MIN_VISIBILITY = 0.45
    DOWN_THRESHOLD = 110
    UP_THRESHOLD = 145
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.reps = 0
        self.stage = "up"
        self._last_rep_time = 0.0

    def process(self, landmarks):
        required = [11, 13, 15, 23, 27]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Body not clearly visible"}

        shoulder = self.get_point(landmarks, 11)
        elbow = self.get_point(landmarks, 13)
        wrist = self.get_point(landmarks, 15)
        hip = self.get_point(landmarks, 23)
        ankle = self.get_point(landmarks, 27)
        elbow_angle = self.calculate_angle(shoulder, elbow, wrist)
        body_angle = self.calculate_angle(shoulder, hip, ankle)

        if self.stage == "up" and elbow_angle <= self.DOWN_THRESHOLD:
            self.stage = "down"
        elif self.stage == "down" and elbow_angle >= self.UP_THRESHOLD:
            now = time.monotonic()
            if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                self.reps += 1
                self._last_rep_time = now
            self.stage = "up"

        body_alignment = "Straight" if body_angle > 155 else "Slight Bend" if body_angle > 130 else "Adjust body"
        return {
            "reps": self.reps, "stage": self.stage,
            "elbow_angle": int(elbow_angle),
            "body_alignment": body_alignment,
            "hip_status": "LEVEL" if body_angle >= 130 else "SAGGING/PIKED",
        }

    def reset(self):
        self.reset_common_state()
        self.reps = 0
        self.stage = "up"
        self._last_rep_time = 0.0

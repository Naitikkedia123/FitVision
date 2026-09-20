from ai_gym.core.base_exercise import BaseExercise


class SitToStandDetector(BaseExercise):
    """Counts controlled sit-to-stand transitions."""

    MIN_VISIBILITY = 0.55
    SIT_THRESHOLD = 120
    STAND_THRESHOLD = 158

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "standing"
        self.reps = 0

    def process(self, landmarks):
        required = [11, 23, 25, 27]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Body not clearly visible"}

        shoulder = self.get_point(landmarks, 11)
        hip = self.get_point(landmarks, 23)
        knee = self.get_point(landmarks, 25)
        ankle = self.get_point(landmarks, 27)

        knee_angle = self.calculate_angle(hip, knee, ankle)
        hip_angle = self.calculate_angle(shoulder, hip, knee)

        if self.stage == "standing" and knee_angle <= self.SIT_THRESHOLD:
            self.stage = "sitting"
        elif self.stage == "sitting" and knee_angle >= self.STAND_THRESHOLD and hip_angle >= 145:
            self.reps += 1
            self.stage = "standing"

        return {
            "reps": self.reps, "stage": self.stage,
            "knee_angle": round(knee_angle, 1),
            "hip_angle": round(hip_angle, 1),
            "status": "Sit down with control" if self.stage == "standing" else "Stand tall",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "standing"
        self.reps = 0

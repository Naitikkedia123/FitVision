from ai_gym.core.base_exercise import BaseExercise


class KneePushUpDetector(BaseExercise):
    """Counts knee push-ups using elbow flexion and shoulder-hip-knee alignment."""

    MIN_VISIBILITY = 0.55
    DOWN_THRESHOLD = 100
    UP_THRESHOLD = 155
    MIN_BODY_ANGLE = 140

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "up"
        self.reps = 0

    def process(self, landmarks):
        required = [11, 13, 15, 23, 25]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Body not clearly visible"}

        shoulder = self.get_point(landmarks, 11)
        elbow = self.get_point(landmarks, 13)
        wrist = self.get_point(landmarks, 15)
        hip = self.get_point(landmarks, 23)
        knee = self.get_point(landmarks, 25)

        elbow_angle = self.calculate_angle(shoulder, elbow, wrist)
        body_angle = self.calculate_angle(shoulder, hip, knee)
        aligned = body_angle >= self.MIN_BODY_ANGLE

        if aligned:
            if self.stage == "up" and elbow_angle <= self.DOWN_THRESHOLD:
                self.stage = "down"
            elif self.stage == "down" and elbow_angle >= self.UP_THRESHOLD:
                self.reps += 1
                self.stage = "up"

        return {
            "reps": self.reps, "stage": self.stage,
            "elbow_angle": round(elbow_angle, 1),
            "body_alignment": round(body_angle, 1),
            "alignment_status": "Good" if aligned else "Adjust body alignment",
            "status": "Lower with control" if self.stage == "up" else "Push back up",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "up"
        self.reps = 0

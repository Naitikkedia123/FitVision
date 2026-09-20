from ai_gym.core.base_exercise import BaseExercise


class WallPushUpDetector(BaseExercise):
    """Counts wall push-ups from a side-view pose."""

    MIN_VISIBILITY = 0.55
    DOWN_THRESHOLD = 105
    UP_THRESHOLD = 155

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "up"
        self.reps = 0

    def process(self, landmarks):
        required = [11, 13, 15, 23]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Upper body not clearly visible"}

        shoulder = self.get_point(landmarks, 11)
        elbow = self.get_point(landmarks, 13)
        wrist = self.get_point(landmarks, 15)
        hip = self.get_point(landmarks, 23)

        elbow_angle = self.calculate_angle(shoulder, elbow, wrist)
        torso_angle = self.calculate_angle(shoulder, hip, elbow)

        if self.stage == "up" and elbow_angle <= self.DOWN_THRESHOLD:
            self.stage = "down"
        elif self.stage == "down" and elbow_angle >= self.UP_THRESHOLD:
            self.reps += 1
            self.stage = "up"

        return {
            "reps": self.reps, "stage": self.stage,
            "elbow_angle": round(elbow_angle, 1),
            "torso_angle": round(torso_angle, 1),
            "status": "Bend your elbows" if self.stage == "up" else "Push away from the wall",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "up"
        self.reps = 0

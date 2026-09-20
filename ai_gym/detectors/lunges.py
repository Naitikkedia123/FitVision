from ai_gym.core.base_exercise import BaseExercise


class LungesDetector(BaseExercise):
    """Counts alternating lunges using the deeper visible knee."""

    MIN_VISIBILITY = 0.55
    DOWN_THRESHOLD = 105
    UP_THRESHOLD = 155

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.reps = 0
        self.stage = "up"
        self.active_side = None

    def process(self, landmarks):
        required = [11, 12, 23, 24, 25, 26, 27, 28]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Body not clearly visible"}

        left = self.calculate_angle(self.get_point(landmarks, 23), self.get_point(landmarks, 25), self.get_point(landmarks, 27))
        right = self.calculate_angle(self.get_point(landmarks, 24), self.get_point(landmarks, 26), self.get_point(landmarks, 28))
        front_angle = min(left, right)
        side = "left" if left <= right else "right"

        shoulder_mid_x = (landmarks[11].x + landmarks[12].x) / 2
        hip_mid_x = (landmarks[23].x + landmarks[24].x) / 2
        balance = abs(shoulder_mid_x - hip_mid_x)

        if self.stage == "up" and front_angle <= self.DOWN_THRESHOLD:
            self.stage = "down"
            self.active_side = side
        elif self.stage == "down" and front_angle >= self.UP_THRESHOLD:
            self.reps += 1
            self.stage = "up"
            self.active_side = None

        return {
            "reps": self.reps, "stage": self.stage,
            "front_knee_angle": int(front_angle),
            "torso_angle": 0,
            "balance_status": "BALANCED" if balance <= 0.12 else "OFF BALANCE",
            "side": self.active_side,
        }

    def reset(self):
        self.reset_common_state()
        self.reps = 0
        self.stage = "up"
        self.active_side = None

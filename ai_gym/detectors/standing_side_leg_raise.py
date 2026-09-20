from ai_gym.core.base_exercise import BaseExercise


class StandingSideLegRaiseDetector(BaseExercise):
    """Counts controlled lateral standing leg raises."""

    MIN_VISIBILITY = 0.55
    RAISE_THRESHOLD = 0.12
    RELEASE_THRESHOLD = 0.07

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "down"
        self.reps = 0
        self.active_side = None

    def process(self, landmarks):
        required = [23, 24, 25, 26, 27, 28]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Body not clearly visible"}

        hip_x = (landmarks[23].x + landmarks[24].x) / 2
        left = abs(landmarks[27].x - hip_x)
        right = abs(landmarks[28].x - hip_x)
        amount = max(left, right)
        side = "left" if left >= right else "right"

        if self.stage == "down" and amount >= self.RAISE_THRESHOLD:
            self.stage = "up"
            self.active_side = side
        elif self.stage == "up":
            active_amount = left if self.active_side == "left" else right
            if active_amount <= self.RELEASE_THRESHOLD:
                self.reps += 1
                self.stage = "down"
                self.active_side = None

        return {
            "reps": self.reps, "stage": self.stage,
            "leg_distance": round(amount, 4),
            "side": self.active_side,
            "status": "Raise your leg to the side" if self.stage == "down" else "Lower your leg",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "down"
        self.reps = 0
        self.active_side = None

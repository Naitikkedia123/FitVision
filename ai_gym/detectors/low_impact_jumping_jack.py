from ai_gym.core.base_exercise import BaseExercise


class LowImpactJumpingJackDetector(BaseExercise):
    """Counts low-impact step-out/step-in jumping jacks."""

    MIN_VISIBILITY = 0.50
    OUT_LEG_RATIO = 1.30
    OUT_ARM_RATIO = 1.75
    IN_LEG_RATIO = 1.10
    IN_ARM_RATIO = 1.45

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "in"
        self.reps = 0

    def process(self, landmarks):
        required = [11, 12, 15, 16, 27, 28]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Body not clearly visible"}

        shoulder_width = max(abs(landmarks[11].x - landmarks[12].x), 0.06)
        ankle_width = abs(landmarks[27].x - landmarks[28].x)
        wrist_width = abs(landmarks[15].x - landmarks[16].x)

        arms_out = wrist_width >= shoulder_width * self.OUT_ARM_RATIO
        legs_out = ankle_width >= shoulder_width * self.OUT_LEG_RATIO
        out = arms_out and legs_out

        arms_in = wrist_width <= shoulder_width * self.IN_ARM_RATIO
        legs_in = ankle_width <= shoulder_width * self.IN_LEG_RATIO
        inside = arms_in and legs_in

        if self.stage == "in" and out:
            self.stage = "out"
        elif self.stage == "out" and inside:
            self.reps += 1
            self.stage = "in"

        return {
            "reps": self.reps, "stage": self.stage,
            "arms_out": arms_out, "legs_out": legs_out,
            "status": "Step out" if self.stage == "in" else "Step back in",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "in"
        self.reps = 0

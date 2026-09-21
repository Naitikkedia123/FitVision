from ai_gym.core.base_exercise import BaseExercise
import time


class LowImpactJumpingJackDetector(BaseExercise):
    """Counts low-impact jumping jacks with relaxed arm/leg spread."""

    MIN_VISIBILITY = 0.45
    OUT_LEG_RATIO = 1.15
    OUT_ARM_RATIO = 1.45
    IN_LEG_RATIO = 1.00
    IN_ARM_RATIO = 1.25
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "in"
        self.reps = 0
        self._last_rep_time = 0.0

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
        arms_in = wrist_width <= shoulder_width * self.IN_ARM_RATIO
        legs_in = ankle_width <= shoulder_width * self.IN_LEG_RATIO
        out = arms_out and legs_out
        inside = arms_in and legs_in

        if self.stage == "in" and out:
            self.stage = "out"
        elif self.stage == "out" and inside:
            now = time.monotonic()
            if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                self.reps += 1
                self._last_rep_time = now
            self.stage = "in"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "arm_width_ratio": round(wrist_width / shoulder_width, 2),
            "leg_width_ratio": round(ankle_width / shoulder_width, 2),
            "status": "Open arms and legs" if self.stage == "in" else "Bring arms and legs back",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "in"
        self.reps = 0
        self._last_rep_time = 0.0

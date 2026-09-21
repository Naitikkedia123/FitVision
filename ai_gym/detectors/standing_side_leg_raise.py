from ai_gym.core.base_exercise import BaseExercise
import time


class StandingSideLegRaiseDetector(BaseExercise):
    """Counts side leg raises with a relaxed lateral movement threshold."""

    MIN_VISIBILITY = 0.45
    RAISE_THRESHOLD = 0.085
    RELEASE_THRESHOLD = 0.060
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.reps = 0
        self.stage = "down"
        self.active_side = None
        self._last_rep_time = 0.0

    def process(self, landmarks):
        required = [23, 24, 27, 28]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if max(getattr(landmarks[i], "visibility", 1.0) for i in required) < self.MIN_VISIBILITY:
            return {"reps": self.reps, "stage": self.stage, "status": "Legs not clearly visible"}

        hip_x = (landmarks[23].x + landmarks[24].x) / 2
        left_amount = abs(landmarks[27].x - hip_x)
        right_amount = abs(landmarks[28].x - hip_x)
        amount = max(left_amount, right_amount)
        side = "left" if left_amount >= right_amount else "right"

        if self.stage == "down" and amount >= self.RAISE_THRESHOLD:
            self.stage = "up"
            self.active_side = side
        elif self.stage == "up":
            active_amount = left_amount if self.active_side == "left" else right_amount
            if active_amount <= self.RELEASE_THRESHOLD:
                now = time.monotonic()
                if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                    self.reps += 1
                    self._last_rep_time = now
                self.stage = "down"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "side_leg_amount": round(amount, 3),
            "side": self.active_side,
            "status": "Raise your leg sideways" if self.stage == "down" else "Return to center",
        }

    def reset(self):
        self.reset_common_state()
        self.reps = 0
        self.stage = "down"
        self.active_side = None
        self._last_rep_time = 0.0

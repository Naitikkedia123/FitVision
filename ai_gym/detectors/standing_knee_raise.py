from ai_gym.core.base_exercise import BaseExercise
import time


class StandingKneeRaiseDetector(BaseExercise):
    """Counts knee raises using simple normalized knee lift."""

    MIN_VISIBILITY = 0.45
    RAISE_THRESHOLD = 0.055
    RELEASE_THRESHOLD = 0.018
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.reps = 0
        self.stage = "down"
        self.active_side = None
        self._last_rep_time = 0.0

    def process(self, landmarks):
        required = [23, 24, 25, 26, 27, 28]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if max(getattr(landmarks[i], "visibility", 1.0) for i in required) < self.MIN_VISIBILITY:
            return {"reps": self.reps, "stage": self.stage, "status": "Legs not clearly visible"}

        hip_y = (landmarks[23].y + landmarks[24].y) / 2
        left_lift = hip_y - landmarks[25].y
        right_lift = hip_y - landmarks[26].y
        lift = max(left_lift, right_lift)
        side = "left" if left_lift >= right_lift else "right"

        if self.stage == "down" and lift >= self.RAISE_THRESHOLD:
            self.stage = "up"
            self.active_side = side
        elif self.stage == "up":
            active_lift = left_lift if self.active_side == "left" else right_lift
            if active_lift <= self.RELEASE_THRESHOLD:
                now = time.monotonic()
                if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                    self.reps += 1
                    self._last_rep_time = now
                self.stage = "down"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "knee_lift": round(lift, 3),
            "side": self.active_side,
            "status": "Lift your knee" if self.stage == "down" else "Lower your knee",
        }

    def reset(self):
        self.reset_common_state()
        self.reps = 0
        self.stage = "down"
        self.active_side = None
        self._last_rep_time = 0.0

from ai_gym.core.base_exercise import BaseExercise


class StandingKneeRaiseDetector(BaseExercise):
    """Counts alternating standing knee raises."""

    MIN_VISIBILITY = 0.55
    RAISE_THRESHOLD = 0.07
    RELEASE_THRESHOLD = 0.025
    STANDING_ANGLE = 135

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "down"
        self.reps = 0
        self.last_side = None
        self.active_side = None

    def process(self, landmarks):
        required = [23, 24, 25, 26, 27, 28]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Body not clearly visible"}

        lh, rh = self.get_point(landmarks, 23), self.get_point(landmarks, 24)
        lk, rk = self.get_point(landmarks, 25), self.get_point(landmarks, 26)
        la, ra = self.get_point(landmarks, 27), self.get_point(landmarks, 28)

        hip_y = (lh[1] + rh[1]) / 2
        left_lift = hip_y - lk[1]
        right_lift = hip_y - rk[1]
        lift = max(left_lift, right_lift)

        left_angle = self.calculate_angle(lh, lk, la)
        right_angle = self.calculate_angle(rh, rk, ra)

        # Only the supporting leg must remain reasonably extended.
        if self.stage == "down" and lift >= self.RAISE_THRESHOLD:
            side = "left" if left_lift >= right_lift else "right"
            if self.last_side is None or side != self.last_side:
                self.active_side = side
                self.stage = "up"
            else:
                # Allow repeated same-side raises if the user naturally performs them.
                self.active_side = side
                self.stage = "up"

        elif self.stage == "up":
            active_lift = left_lift if self.active_side == "left" else right_lift
            if active_lift <= self.RELEASE_THRESHOLD:
                self.reps += 1
                self.last_side = self.active_side
                self.active_side = None
                self.stage = "down"

        return {
            "reps": self.reps, "stage": self.stage,
            "knee_lift": round(lift, 4),
            "side": self.active_side or self.last_side,
            "left_knee_angle": round(left_angle, 1),
            "right_knee_angle": round(right_angle, 1),
            "status": "Raise a knee" if self.stage == "down" else "Lower your knee",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "down"
        self.reps = 0
        self.last_side = None
        self.active_side = None

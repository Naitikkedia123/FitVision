from ai_gym.core.base_exercise import BaseExercise


class HipExtensionDetector(BaseExercise):
    """Counts controlled standing hip extensions using relative leg displacement."""

    MIN_VISIBILITY = 0.55
    EXTEND_THRESHOLD = 0.10
    RELEASE_THRESHOLD = 0.5

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "neutral"
        self.reps = 0
        self.active_side = None

    def process(self, landmarks):
        required = [23, 24, 25, 26, 27, 28]

        if landmarks is None or len(landmarks) <= max(required):
            return {
                "reps": self.reps,
                "stage": self.stage,
                "status": "Landmarks unavailable",
            }

        if any(
            getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY
            for i in required
        ):
            return {
                "reps": self.reps,
                "stage": self.stage,
                "status": "Body not clearly visible",
            }

        # Positive value means the leg has moved backward
        # relative to its corresponding hip.
        left_extension = landmarks[27].x - landmarks[23].x
        right_extension = landmarks[24].x - landmarks[28].x

        extension = max(left_extension, right_extension)

        if self.stage == "neutral" and extension >= self.EXTEND_THRESHOLD:
            self.stage = "extended"
            self.active_side = (
                "left" if left_extension >= right_extension else "right"
            )

        elif self.stage == "extended" and extension <= self.RELEASE_THRESHOLD:
            self.reps += 1
            self.stage = "neutral"
            self.active_side = None

        return {
            "reps": self.reps,
            "stage": self.stage,
            "extension": round(extension, 4),
            "side": self.active_side,
            "status": (
                "Extend one leg backward"
                if self.stage == "neutral"
                else "Return to neutral"
            ),
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "neutral"
        self.reps = 0
        self.active_side = None
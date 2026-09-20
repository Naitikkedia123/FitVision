from ai_gym.core.base_exercise import BaseExercise


class HamstringCurlDetector(BaseExercise):
    """Counts standing hamstring curls, one completed curl per leg."""

    MIN_VISIBILITY = 0.55
    CURL_THRESHOLD = 125
    RELEASE_THRESHOLD = 155

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

        la = self.calculate_angle(self.get_point(landmarks, 23), self.get_point(landmarks, 25), self.get_point(landmarks, 27))
        ra = self.calculate_angle(self.get_point(landmarks, 24), self.get_point(landmarks, 26), self.get_point(landmarks, 28))

        if self.stage == "down":
            if la <= self.CURL_THRESHOLD and la <= ra:
                self.stage, self.active_side = "up", "left"
            elif ra <= self.CURL_THRESHOLD:
                self.stage, self.active_side = "up", "right"
        elif self.stage == "up":
            current = la if self.active_side == "left" else ra
            if current >= self.RELEASE_THRESHOLD:
                self.reps += 1
                self.stage = "down"

        angle = la if self.active_side == "left" else ra if self.active_side == "right" else min(la, ra)

        return {
            "reps": self.reps, "stage": self.stage,
            "knee_angle": round(angle, 1), "side": self.active_side,
            "status": "Curl your heel upward" if self.stage == "down" else "Lower your leg",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "down"
        self.reps = 0
        self.active_side = None

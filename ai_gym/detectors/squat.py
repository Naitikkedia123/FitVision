from ai_gym.core.base_exercise import BaseExercise
import time


class SquatDetector(BaseExercise):
    """Counts practical bodyweight squats with relaxed depth thresholds."""

    DOWN_THRESHOLD = 115
    UP_THRESHOLD = 145
    MIN_VISIBILITY = 0.55
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "up"
        self.reps = 0
        self._last_rep_time = 0.0

    def process(self, landmarks):
        required = [11, 12, 23, 24, 25, 26, 27, 28]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}

        left_vis = min(getattr(landmarks[i], "visibility", 1.0) for i in (23, 25, 27))
        right_vis = min(getattr(landmarks[i], "visibility", 1.0) for i in (24, 26, 28))
        if max(left_vis, right_vis) < self.MIN_VISIBILITY:
            return {"reps": self.reps, "stage": self.stage, "status": "Legs not clearly visible"}

        if left_vis >= right_vis:
            hip, knee, ankle = 23, 25, 27
        else:
            hip, knee, ankle = 24, 26, 28

        knee_angle = self.calculate_angle(self.get_point(landmarks, hip), self.get_point(landmarks, knee), self.get_point(landmarks, ankle))
        hip_angle = self.calculate_angle(self.get_point(landmarks, 11 if hip == 23 else 12), self.get_point(landmarks, hip), self.get_point(landmarks, knee))

        if self.stage == "up" and knee_angle <= self.DOWN_THRESHOLD:
            self.stage = "down"
        elif self.stage == "down" and knee_angle >= self.UP_THRESHOLD:
            now = time.monotonic()
            if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                self.reps += 1
                self._last_rep_time = now
            self.stage = "up"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "knee_angle": round(knee_angle, 1),
            "hip_angle": round(hip_angle, 1),
            "depth_status": "GOOD DEPTH" if knee_angle <= self.DOWN_THRESHOLD else "READY",
            "status": "Stand up" if self.stage == "down" else "Lower into squat",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "up"
        self.reps = 0
        self._last_rep_time = 0.0

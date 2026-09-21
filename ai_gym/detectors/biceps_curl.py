from ai_gym.core.base_exercise import BaseExercise
import math
import time


class BicepsCurlDetector(BaseExercise):
    """Counts practical biceps curls with relaxed motion thresholds."""

    UP_THRESHOLD = 75
    DOWN_THRESHOLD = 135
    MIN_VISIBILITY = 0.45
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.reps = 0
        self.stage = "down"
        self.active_side = None
        self._last_rep_time = 0.0

    def reset(self):
        self.reset_common_state()
        self.reps = 0
        self.stage = "down"
        self.active_side = None
        self._last_rep_time = 0.0

    def process(self, landmarks):
        required = [11, 12, 13, 14, 15, 16]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}

        visible = {i: getattr(landmarks[i], "visibility", 1.0) for i in required}
        candidates = []
        for side, s, e, w in (("left", 11, 13, 15), ("right", 12, 14, 16)):
            if min(visible[s], visible[e], visible[w]) >= self.MIN_VISIBILITY:
                candidates.append((visible[s] + visible[e] + visible[w], side, s, e, w))

        if not candidates:
            return {"reps": self.reps, "stage": self.stage, "status": "Arm not clearly visible"}

        _, side, s, e, w = max(candidates)
        shoulder = self.get_point(landmarks, s)
        elbow = self.get_point(landmarks, e)
        wrist = self.get_point(landmarks, w)
        angle = self.calculate_angle(shoulder, elbow, wrist)

        drift = abs(elbow[0] - shoulder[0])
        shoulder_mid_x = (landmarks[11].x + landmarks[12].x) / 2
        shoulder_mid_y = (landmarks[11].y + landmarks[12].y) / 2
        hip_mid_x = (landmarks[23].x + landmarks[24].x) / 2
        hip_mid_y = (landmarks[23].y + landmarks[24].y) / 2
        swing = math.degrees(math.atan2(abs(shoulder_mid_x - hip_mid_x), abs(shoulder_mid_y - hip_mid_y) + 1e-6))

        if self.stage == "down" and angle <= self.UP_THRESHOLD:
            self.stage = "up"
            self.active_side = side
        elif self.stage == "up" and angle >= self.DOWN_THRESHOLD:
            now = time.monotonic()
            if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                self.reps += 1
                self._last_rep_time = now
            self.stage = "down"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "elbow_angle": int(angle),
            "shoulder_status": "STABLE" if drift <= 0.14 else "ELBOW DRIFTING",
            "swing_status": "NO SWING" if swing <= 30 else "SWINGING",
            "side": self.active_side,
        }

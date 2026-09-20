from ai_gym.core.base_exercise import BaseExercise
import math


class BicepsCurlDetector(BaseExercise):
    """Counts controlled dumbbell biceps curls using the better-visible arm."""

    UP_THRESHOLD = 55
    DOWN_THRESHOLD = 155
    MIN_VISIBILITY = 0.60
    ELBOW_DRIFT_TOLERANCE = 0.08
    SWING_THRESHOLD = 18

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.reps = 0
        self.stage = "down"
        self.active_side = None

    def reset(self):
        self.reset_common_state()
        self.reps = 0
        self.stage = "down"
        self.active_side = None

    def process(self, landmarks):
        required = [11, 12, 13, 14, 15, 16, 23, 24]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage,
                    "status": "Landmarks unavailable"}

        visible = {i: getattr(landmarks[i], "visibility", 1.0) for i in required}
        if max(visible[13], visible[14]) < self.MIN_VISIBILITY:
            return {"reps": self.reps, "stage": self.stage,
                    "status": "Arms not clearly visible"}

        if visible[13] >= visible[14]:
            side = "left"
            s, e, w = 11, 13, 15
        else:
            side = "right"
            s, e, w = 12, 14, 16

        if min(visible[s], visible[e], visible[w]) < self.MIN_VISIBILITY:
            return {"reps": self.reps, "stage": self.stage,
                    "status": "Arm not clearly visible"}

        shoulder = self.get_point(landmarks, s)
        elbow = self.get_point(landmarks, e)
        wrist = self.get_point(landmarks, w)

        angle = self.calculate_angle(shoulder, elbow, wrist)
        drift = abs(elbow[0] - shoulder[0])

        shoulder_mid_x = (landmarks[11].x + landmarks[12].x) / 2
        shoulder_mid_y = (landmarks[11].y + landmarks[12].y) / 2
        hip_mid_x = (landmarks[23].x + landmarks[24].x) / 2
        hip_mid_y = (landmarks[23].y + landmarks[24].y) / 2

        swing = math.degrees(
            math.atan2(abs(shoulder_mid_x - hip_mid_x),
                       abs(shoulder_mid_y - hip_mid_y) + 1e-6)
        )

        if self.stage == "down" and angle <= self.UP_THRESHOLD:
            self.stage = "up"
            self.active_side = side
        elif self.stage == "up" and angle >= self.DOWN_THRESHOLD:
            self.reps += 1
            self.stage = "down"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "elbow_angle": int(angle),
            "shoulder_status": "STABLE" if drift <= self.ELBOW_DRIFT_TOLERANCE else "ELBOW DRIFTING",
            "swing_status": "NO SWING" if swing <= self.SWING_THRESHOLD else "SWINGING",
            "side": self.active_side,
        }

from ai_gym.core.base_exercise import BaseExercise


class ShoulderPressDetector(BaseExercise):
    """Counts controlled overhead shoulder presses."""

    MIN_VISIBILITY = 0.55
    UP_THRESHOLD = 160
    DOWN_THRESHOLD = 90

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.reps = 0
        self.stage = "down"

    def process(self, landmarks):
        required = [11, 12, 13, 14, 15, 16, 23, 24]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if max(getattr(landmarks[13], "visibility", 1.0),
               getattr(landmarks[14], "visibility", 1.0)) < self.MIN_VISIBILITY:
            return {"reps": self.reps, "stage": self.stage, "status": "Arms not clearly visible"}

        left_angle = self.calculate_angle(self.get_point(landmarks, 11), self.get_point(landmarks, 13), self.get_point(landmarks, 15))
        right_angle = self.calculate_angle(self.get_point(landmarks, 12), self.get_point(landmarks, 14), self.get_point(landmarks, 16))
        angles = [left_angle, right_angle]
        visible_angles = [
            a for a, i in zip(angles, [13, 14])
            if getattr(landmarks[i], "visibility", 1.0) >= self.MIN_VISIBILITY
        ]
        angle = sum(visible_angles) / len(visible_angles)

        if self.stage == "down" and angle >= self.UP_THRESHOLD:
            self.stage = "up"
        elif self.stage == "up" and angle <= self.DOWN_THRESHOLD:
            self.reps += 1
            self.stage = "down"

        hip_y = (landmarks[23].y + landmarks[24].y) / 2
        shoulder_y = (landmarks[11].y + landmarks[12].y) / 2
        torso_lean = abs(shoulder_y - hip_y)

        return {
            "reps": self.reps, "stage": self.stage,
            "elbow_angle": int(angle),
            "extension_status": "FULL EXTENSION" if angle >= 160 else "NEARLY EXTENDED" if angle >= 130 else "PRESSING",
            "back_arch_status": "Neutral" if torso_lean < 0.18 else "Check posture",
        }

    def reset(self):
        self.reset_common_state()
        self.reps = 0
        self.stage = "down"

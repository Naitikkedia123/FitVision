from ai_gym.core.base_exercise import BaseExercise
import time


class ShoulderPressDetector(BaseExercise):
    """Counts shoulder presses with relaxed extension/flexion thresholds."""

    MIN_VISIBILITY = 0.45
    UP_THRESHOLD = 145
    DOWN_THRESHOLD = 105
    MIN_REP_INTERVAL = 0.30

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.reps = 0
        self.stage = "down"
        self._last_rep_time = 0.0

    def process(self, landmarks):
        required = [11, 12, 13, 14, 15, 16]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}

        left_visible = min(getattr(landmarks[i], "visibility", 1.0) for i in (11, 13, 15)) >= self.MIN_VISIBILITY
        right_visible = min(getattr(landmarks[i], "visibility", 1.0) for i in (12, 14, 16)) >= self.MIN_VISIBILITY
        if not left_visible and not right_visible:
            return {"reps": self.reps, "stage": self.stage, "status": "Arms not clearly visible"}

        angles = []
        if left_visible:
            angles.append(self.calculate_angle(self.get_point(landmarks, 11), self.get_point(landmarks, 13), self.get_point(landmarks, 15)))
        if right_visible:
            angles.append(self.calculate_angle(self.get_point(landmarks, 12), self.get_point(landmarks, 14), self.get_point(landmarks, 16)))
        angle = sum(angles) / len(angles)

        if self.stage == "down" and angle >= self.UP_THRESHOLD:
            self.stage = "up"
        elif self.stage == "up" and angle <= self.DOWN_THRESHOLD:
            now = time.monotonic()
            if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                self.reps += 1
                self._last_rep_time = now
            self.stage = "down"

        hip_y = (landmarks[23].y + landmarks[24].y) / 2
        shoulder_y = (landmarks[11].y + landmarks[12].y) / 2
        torso_lean = abs(shoulder_y - hip_y)

        return {
            "reps": self.reps,
            "stage": self.stage,
            "elbow_angle": int(angle),
            "extension_status": "FULL EXTENSION" if angle >= 145 else "NEARLY EXTENDED" if angle >= 125 else "PRESSING",
            "back_arch_status": "Neutral" if torso_lean < 0.22 else "Check posture",
        }

    def reset(self):
        self.reset_common_state()
        self.reps = 0
        self.stage = "down"
        self._last_rep_time = 0.0

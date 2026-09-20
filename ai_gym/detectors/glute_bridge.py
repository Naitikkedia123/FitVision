from ai_gym.core.base_exercise import BaseExercise


class GluteBridgeDetector(BaseExercise):
    """Counts glute bridges from a side-view pose."""

    MIN_VISIBILITY = 0.55
    UP_HIP_ANGLE = 150
    DOWN_HIP_ANGLE = 125
    MIN_KNEE_ANGLE = 65
    MAX_KNEE_ANGLE = 155

    def __init__(self):
        super().__init__(measurement_type="reps")
        self.stage = "down"
        self.reps = 0

    def process(self, landmarks):
        required = [11, 23, 25, 27]
        if landmarks is None or len(landmarks) <= max(required):
            return {"reps": self.reps, "stage": self.stage, "status": "Landmarks unavailable"}
        if any(getattr(landmarks[i], "visibility", 1.0) < self.MIN_VISIBILITY for i in required):
            return {"reps": self.reps, "stage": self.stage, "status": "Body not clearly visible"}

        shoulder = self.get_point(landmarks, 11)
        hip = self.get_point(landmarks, 23)
        knee = self.get_point(landmarks, 25)
        ankle = self.get_point(landmarks, 27)

        hip_angle = self.calculate_angle(shoulder, hip, knee)
        knee_angle = self.calculate_angle(hip, knee, ankle)
        raised = hip_angle >= self.UP_HIP_ANGLE and self.MIN_KNEE_ANGLE <= knee_angle <= self.MAX_KNEE_ANGLE

        if self.stage == "down" and raised:
            self.stage = "up"
        elif self.stage == "up" and hip_angle <= self.DOWN_HIP_ANGLE:
            self.reps += 1
            self.stage = "down"

        return {
            "reps": self.reps, "stage": self.stage,
            "knee_angle": round(knee_angle, 1),
            "hip_angle": round(hip_angle, 1),
            "status": "Lift your hips" if self.stage == "down" else "Lower with control",
        }

    def reset(self):
        self.reset_common_state()
        self.stage = "down"
        self.reps = 0

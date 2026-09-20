import math

from ai_gym.core.base_exercise import BaseExercise


class CalfRaiseDetector(BaseExercise):
    """
    Easy-to-detect standing calf raise detector.

    Uses leg geometry instead of toes/heel movement.

    Main idea:
    - Keep the person roughly upright.
    - Measure the angle of each knee.
    - Track the relative ankle position against the leg.
    - A noticeable upward change puts the detector into "up".
    - Returning toward the standing position counts one rep.

    This version intentionally uses relaxed thresholds because
    real-camera detection is the priority.
    """

    MIN_VISIBILITY = 0.45

    # Very relaxed movement thresholds.
    LIFT_THRESHOLD = 0.025
    RELEASE_THRESHOLD = 0.012

    # Prevent repeated counting from noisy frames.
    MIN_REP_INTERVAL = 0.35

    def __init__(self):
        super().__init__(measurement_type="reps")

        self.stage = "down"
        self.reps = 0

        self._baseline = None
        self._last_rep_time = 0.0

    # ---------------------------------------------------------
    # Geometry helpers
    # ---------------------------------------------------------

    @staticmethod
    def _distance(a, b):
        return math.sqrt(
            (a.x - b.x) ** 2 +
            (a.y - b.y) ** 2
        )

    @staticmethod
    def _angle(a, b, c):
        """
        Angle ABC in degrees.
        """
        ba_x = a.x - b.x
        ba_y = a.y - b.y

        bc_x = c.x - b.x
        bc_y = c.y - b.y

        mag_ba = math.sqrt(ba_x ** 2 + ba_y ** 2)
        mag_bc = math.sqrt(bc_x ** 2 + bc_y ** 2)

        if mag_ba == 0 or mag_bc == 0:
            return 180.0

        dot = ba_x * bc_x + ba_y * bc_y

        cos_angle = dot / (mag_ba * mag_bc)
        cos_angle = max(-1.0, min(1.0, cos_angle))

        return math.degrees(math.acos(cos_angle))

    # ---------------------------------------------------------
    # Main detector
    # ---------------------------------------------------------

    def process(self, landmarks):
        required = [23, 24, 25, 26, 27, 28]

        if landmarks is None or len(landmarks) <= max(required):
            return {
                "reps": self.reps,
                "stage": self.stage,
                "status": "Landmarks unavailable",
            }

        # -----------------------------------------------------
        # Visibility check
        # -----------------------------------------------------

        for idx in required:
            visibility = getattr(landmarks[idx], "visibility", 1.0)

            if visibility < self.MIN_VISIBILITY:
                return {
                    "reps": self.reps,
                    "stage": self.stage,
                    "status": "Legs not clearly visible",
                }

        left_hip = landmarks[23]
        right_hip = landmarks[24]

        left_knee = landmarks[25]
        right_knee = landmarks[26]

        left_ankle = landmarks[27]
        right_ankle = landmarks[28]

        # -----------------------------------------------------
        # Knee angles
        # -----------------------------------------------------

        left_knee_angle = self._angle(
            left_hip,
            left_knee,
            left_ankle,
        )

        right_knee_angle = self._angle(
            right_hip,
            right_knee,
            right_ankle,
        )

        average_knee_angle = (
            left_knee_angle + right_knee_angle
        ) / 2.0

        # -----------------------------------------------------
        # Basic standing check
        #
        # We don't require a perfect standing pose.
        # This only rejects obvious deep squats.
        # -----------------------------------------------------

        if average_knee_angle < 105:
            self.stage = "down"

            return {
                "reps": self.reps,
                "stage": self.stage,
                "knee_angle": round(average_knee_angle, 2),
                "status": "Stand upright",
            }

        # -----------------------------------------------------
        # Build a stable leg-geometry measurement.
        #
        # Instead of trusting toes/heels, compare ankle
        # position with the hip/knee geometry.
        # -----------------------------------------------------

        left_leg_length = self._distance(
            left_knee,
            left_ankle,
        )

        right_leg_length = self._distance(
            right_knee,
            right_ankle,
        )

        left_upper_leg = self._distance(
            left_hip,
            left_knee,
        )

        right_upper_leg = self._distance(
            right_hip,
            right_knee,
        )

        left_total_leg = left_upper_leg + left_leg_length
        right_total_leg = right_upper_leg + right_leg_length

        if left_total_leg <= 0 or right_total_leg <= 0:
            return {
                "reps": self.reps,
                "stage": self.stage,
                "status": "Invalid leg geometry",
            }

        # -----------------------------------------------------
        # Normalized ankle height.
        #
        # This avoids using raw pixel distance.
        # -----------------------------------------------------

        left_ankle_ratio = (
            left_knee.y - left_ankle.y
        ) / left_total_leg

        right_ankle_ratio = (
            right_knee.y - right_ankle.y
        ) / right_total_leg

        ankle_ratio = (
            left_ankle_ratio +
            right_ankle_ratio
        ) / 2.0

        # -----------------------------------------------------
        # Establish baseline.
        #
        # We continuously allow a small adaptation so the
        # detector works for different camera distances.
        # -----------------------------------------------------

        if self._baseline is None:
            self._baseline = ankle_ratio

        else:
            # Slow adaptation only while detector is down.
            if self.stage == "down":
                self._baseline = (
                    self._baseline * 0.98 +
                    ankle_ratio * 0.02
                )

        movement = ankle_ratio - self._baseline

        # -----------------------------------------------------
        # CALF RAISE UP
        # -----------------------------------------------------

        if self.stage == "down":

            if movement >= self.LIFT_THRESHOLD:

                self.stage = "up"

        # -----------------------------------------------------
        # RETURN DOWN → COUNT REP
        # -----------------------------------------------------

        elif self.stage == "up":

            if movement <= self.RELEASE_THRESHOLD:

                now = __import__("time").time()

                if now - self._last_rep_time >= self.MIN_REP_INTERVAL:
                    self.reps += 1
                    self._last_rep_time = now

                self.stage = "down"

        return {
            "reps": self.reps,
            "stage": self.stage,
            "knee_angle": round(average_knee_angle, 2),
            "ankle_ratio": round(ankle_ratio, 4),
            "baseline": round(self._baseline, 4),
            "movement": round(movement, 4),
            "status": (
                "Raise your heels"
                if self.stage == "down"
                else "Lower your heels"
            ),
        }

    # ---------------------------------------------------------
    # Reset
    # ---------------------------------------------------------

    def reset(self):
        self.reset_common_state()

        self.stage = "down"
        self.reps = 0

        self._baseline = None
        self._last_rep_time = 0.0
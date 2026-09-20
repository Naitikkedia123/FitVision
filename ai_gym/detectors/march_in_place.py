import time

from ai_gym.core.base_exercise import BaseExercise


class MarchInPlaceDetector(BaseExercise):
    """
    Tracks cumulative marching time.

    The timer does not reset because of a single bad frame.
    Timing pauses only after marching has been inactive for a
    short continuous period.
    """

    KNEE_RAISE_THRESHOLD = 0.04
    KNEE_RELEASE_THRESHOLD = 0.025

    STEP_COOLDOWN_SECONDS = 0.20
    MARCH_TIMEOUT_SECONDS = 1.50

    def __init__(self):
        super().__init__(measurement_type="time")

        self.stage = "not_marching"
        self.duration_seconds = 0.0

        self._start_time = None
        self._accumulated_duration = 0.0

        self._left_knee_raised = False
        self._right_knee_raised = False

        self._last_step_time = None
        self._last_knee = None
        self._last_valid_time = None

    def process(self, landmarks):
        required = [23, 24, 25, 26]
        now = time.monotonic()

        # -----------------------------------------------------
        # Landmarks unavailable
        # -----------------------------------------------------

        if (
            landmarks is None
            or len(landmarks) <= max(required)
        ):
            self._handle_missing_frame(now)

            return {
                "duration_seconds": round(
                    self.duration_seconds,
                    2,
                ),
                "stage": self.stage,
                "status": "Landmarks unavailable",
            }

        # -----------------------------------------------------
        # Visibility check
        # -----------------------------------------------------

        if any(
            getattr(
                landmarks[i],
                "visibility",
                1.0,
            ) < 0.5
            for i in required
        ):
            self._handle_missing_frame(now)

            return {
                "duration_seconds": round(
                    self.duration_seconds,
                    2,
                ),
                "stage": self.stage,
                "status": "Body not clearly visible",
            }

        self._last_valid_time = now

        # -----------------------------------------------------
        # Hip midpoint
        # -----------------------------------------------------

        hip_y = (
            landmarks[23].y
            + landmarks[24].y
        ) / 2

        # -----------------------------------------------------
        # Knee lift
        # -----------------------------------------------------

        left_lift = (
            hip_y
            - landmarks[25].y
        )

        right_lift = (
            hip_y
            - landmarks[26].y
        )

        # -----------------------------------------------------
        # Detect knee transitions
        # -----------------------------------------------------

        left_step = self._update_left_knee(
            left_lift
        )

        right_step = self._update_right_knee(
            right_lift
        )

        step_detected = False
        detected_knee = None

        if left_step:
            step_detected = True
            detected_knee = "left"

        if right_step:
            step_detected = True

            if detected_knee is None:
                detected_knee = "right"

        # -----------------------------------------------------
        # Prefer alternating knees
        # -----------------------------------------------------

        if step_detected:

            if (
                self._last_knee is not None
                and detected_knee == self._last_knee
            ):
                # Same knee can still be accepted after the
                # cooldown. This prevents the detector from
                # becoming too strict for slower marching.
                pass

            if (
                self._last_step_time is None
                or (
                    now - self._last_step_time
                    >= self.STEP_COOLDOWN_SECONDS
                )
            ):
                self._last_step_time = now
                self._last_knee = detected_knee

                if self._start_time is None:
                    self._start_time = now

                self.stage = "marching"

        # -----------------------------------------------------
        # Continue timing while marching remains active
        # -----------------------------------------------------

        if self._start_time is not None:

            if (
                self._last_step_time is not None
                and (
                    now - self._last_step_time
                    <= self.MARCH_TIMEOUT_SECONDS
                )
            ):
                self.duration_seconds = (
                    self._accumulated_duration
                    + (
                        now
                        - self._start_time
                    )
                )

                self.stage = "marching"

            else:
                self._pause(now)

        # -----------------------------------------------------
        # No timer started yet
        # -----------------------------------------------------

        if self._start_time is None:
            self.duration_seconds = (
                self._accumulated_duration
            )

        if self.stage == "marching":
            status = "Keep marching"
        else:
            status = "Lift your knees and march"

        return {
            "duration_seconds": round(
                self.duration_seconds,
                2,
            ),
            "stage": self.stage,
            "left_knee_lift": round(
                left_lift,
                4,
            ),
            "right_knee_lift": round(
                right_lift,
                4,
            ),
            "knee_lift": round(
                max(
                    left_lift,
                    right_lift,
                ),
                4,
            ),
            "last_knee": self._last_knee,
            "status": status,
        }

    def _update_left_knee(self, lift):
        """
        Detect a left knee raise transition.
        """

        if not self._left_knee_raised:

            if lift >= self.KNEE_RAISE_THRESHOLD:
                self._left_knee_raised = True
                return True

        else:

            if lift <= self.KNEE_RELEASE_THRESHOLD:
                self._left_knee_raised = False

        return False

    def _update_right_knee(self, lift):
        """
        Detect a right knee raise transition.
        """

        if not self._right_knee_raised:

            if lift >= self.KNEE_RAISE_THRESHOLD:
                self._right_knee_raised = True
                return True

        else:

            if lift <= self.KNEE_RELEASE_THRESHOLD:
                self._right_knee_raised = False

        return False

    def _handle_missing_frame(self, now):
        """
        Do not immediately reset timing because of one bad frame.

        The accumulated duration is preserved. The timer is paused
        only when the detector has been inactive long enough.
        """

        if self._start_time is None:
            return

        if (
            self._last_valid_time is not None
            and (
                now - self._last_valid_time
                <= self.MARCH_TIMEOUT_SECONDS
            )
        ):
            self.duration_seconds = (
                self._accumulated_duration
                + (
                    now
                    - self._start_time
                )
            )

            return

        self._pause(now)

    def _pause(self, now):
        """
        Pause timing without losing accumulated duration.
        """

        if self._start_time is not None:

            self._accumulated_duration += (
                now - self._start_time
            )

            self._start_time = None

        self.duration_seconds = (
            self._accumulated_duration
        )

        self.stage = "not_marching"

    def reset(self):
        self.reset_common_state()

        self.stage = "not_marching"
        self.duration_seconds = 0.0

        self._start_time = None
        self._accumulated_duration = 0.0

        self._left_knee_raised = False
        self._right_knee_raised = False

        self._last_step_time = None
        self._last_knee = None
        self._last_valid_time = None
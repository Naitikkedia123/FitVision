import math
from abc import ABC, abstractmethod


class BaseExercise(ABC):
    """
    Common base class for all exercise detectors.

    An exercise can be measured either by:
        - reps
        - time

    Existing detectors default to rep-based measurement, so this remains
    backward compatible with the current 5 exercises.
    """

    def __init__(self, measurement_type="reps"):
        self.reps = 0
        self.stage = None

        # Supported values:
        # "reps"
        # "time"
        self.measurement_type = measurement_type

        # Used by time-based exercises.
        # Individual time-based detectors can update this value.
        self.duration_seconds = 0.0

    @property
    def is_rep_based(self):
        return self.measurement_type == "reps"

    @property
    def is_time_based(self):
        return self.measurement_type == "time"

    def calculate_angle(self, a, b, c):
        ax, ay = a[0] - b[0], a[1] - b[1]
        cx, cy = c[0] - b[0], c[1] - b[1]

        dot = ax * cx + ay * cy

        mag_a = math.sqrt(ax ** 2 + ay ** 2)
        mag_c = math.sqrt(cx ** 2 + cy ** 2)

        if mag_a * mag_c == 0:
            return 0.0

        cos_angle = max(-1.0, min(1.0, dot / (mag_a * mag_c)))

        return math.degrees(math.acos(cos_angle))

    def get_point(self, landmarks, idx):
        p = landmarks[idx]
        return (p.x, p.y)

    def reset_common_state(self):
        """
        Reset state shared by all exercise types.

        Individual detectors can call this from their reset() method if
        they want to use the common reset behavior.
        """
        self.reps = 0
        self.stage = None
        self.duration_seconds = 0.0

    @abstractmethod
    def process(self, landmarks):
        pass

    @abstractmethod
    def reset(self):
        pass
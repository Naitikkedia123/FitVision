from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any

from models.user_profile import UserProfile

@dataclass(frozen=True)
class DosagePrediction:
    """
    Raw dosage prediction produced by the ML model.

    Exactly one of:
        reps
        duration_seconds

    should be populated depending on the exercise's
    measurement type.
    """

    exercise_id: str
    sets: float

    reps: float | None = None
    duration_seconds: float | None = None

    def validate_structure(self) -> None:
        """
        Validate the basic prediction structure.

        This does NOT check whether the values are safe.
        Safety/range validation belongs to dosage_validator.py.
        """

        if not self.exercise_id:
            raise ValueError(
                "exercise_id cannot be empty."
            )

        if self.sets is None:
            raise ValueError(
                "sets cannot be None."
            )

        has_reps = self.reps is not None
        has_duration = self.duration_seconds is not None

        if has_reps == has_duration:
            raise ValueError(
                "Exactly one of reps or duration_seconds "
                "must be provided."
            )

        if not isinstance(self.sets, (int, float)):
            raise TypeError(
                "sets must be numeric."
            )

        if has_reps and not isinstance(
            self.reps,
            (int, float),
        ):
            raise TypeError(
                "reps must be numeric."
            )

        if has_duration and not isinstance(
            self.duration_seconds,
            (int, float),
        ):
            raise TypeError(
                "duration_seconds must be numeric."
            )

class Week1DosagePredictor(ABC):
    """
    Interface for predicting Week-1 dosage.

    The actual implementation can later use a trained ML model.
    """

    @abstractmethod
    def predict(
        self,
        user: UserProfile,
        exercise: dict[str, Any],
    ) -> DosagePrediction:
        """
        Predict the Week-1 dosage for one eligible exercise.
        """
        raise NotImplementedError
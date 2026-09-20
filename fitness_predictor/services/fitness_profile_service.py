from datetime import date
from typing import Any

from database.repositories.fitness_profile_repository import (
    FitnessProfileRepository,
)


class FitnessProfileService:
    """
    Application-level service for managing a user's fitness profile.

    The frontend should use this service instead of directly
    interacting with the repository.
    """

    def __init__(self):
        self.repository = FitnessProfileRepository()

    def create_profile(
        self,
        user_id: str,
        date_of_birth: date | str,
        sex: str,
        height_cm: float,
        weight_kg: float,
        fitness_level: int,
        activity_level: int,
        goal: str,
        workout_time_min: int,
    ) -> dict[str, Any]:
        """
        Create a user's fitness profile.
        """

        existing = self.repository.get_by_user_id(user_id)

        if existing is not None:
            raise ValueError(
                "A fitness profile already exists for this user."
            )

        return self.repository.create(
            user_id=user_id,
            date_of_birth=date_of_birth,
            sex=sex,
            height_cm=height_cm,
            weight_kg=weight_kg,
            fitness_level=fitness_level,
            activity_level=activity_level,
            goal=goal,
            workout_time_min=workout_time_min,
        )

    def get_profile(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """
        Get the user's fitness profile.
        """

        return self.repository.get_by_user_id(user_id)

    def update_profile(
        self,
        user_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update an existing fitness profile.
        """

        return self.repository.update(
            user_id=user_id,
            updates=updates,
        )

    @staticmethod
    def calculate_bmi(
        height_cm: float,
        weight_kg: float,
    ) -> float:
        """
        Calculate BMI from height and weight.

        BMI is calculated when needed rather than stored in the DB.
        """

        if height_cm <= 0:
            raise ValueError("height_cm must be greater than 0.")

        if weight_kg <= 0:
            raise ValueError("weight_kg must be greater than 0.")

        height_m = height_cm / 100

        return round(
            weight_kg / (height_m * height_m),
            2,
        )
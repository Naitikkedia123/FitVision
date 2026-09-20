from typing import Any

from database.repositories.eligibility_repository import (
    EligibilityRepository,
)
from models.user_profile import UserProfile
from rules.functional_eligibility import (
    filter_by_functional_restrictions,
)
from rules.plan_selector import get_difficulty_range


class EligibilityService:
    """
    Builds the user's eligible exercise pool.

    Filtering order:

    1. Apply database-backed exercise exclusion relationships
       for the user's reported limitations.
    2. Apply explicit functional restrictions.
    3. Apply fitness-level difficulty filtering.

    This class does not decide dosage.
    """

    def __init__(self):
        self.exercise_repository = EligibilityRepository()

    def get_eligible_exercises(
        self,
        user: UserProfile,
    ) -> list[dict[str, Any]]:
        """
        Return exercises suitable for the supplied user profile.
        """

        if not isinstance(user, UserProfile):
            raise TypeError(
                "user must be an instance of UserProfile."
            )

        # -----------------------------------------------------
        # 1. Limitation-based database exclusions
        # -----------------------------------------------------

        exercises = (
            self.exercise_repository.get_eligible_exercises(
                user.limitations
            )
        )

        # -----------------------------------------------------
        # 2. Explicit functional restrictions
        # -----------------------------------------------------

        exercises = filter_by_functional_restrictions(
            exercises,
            user.functional_restrictions,
        )

        # -----------------------------------------------------
        # 3. Fitness-level difficulty filtering
        # -----------------------------------------------------

        min_difficulty, max_difficulty = get_difficulty_range(
            user.fitness_level
        )

        return [
            exercise
            for exercise in exercises
            if (
                min_difficulty
                <= exercise["difficulty"]
                <= max_difficulty
            )
        ]
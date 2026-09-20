from dataclasses import dataclass, field
from typing import List
from rules.functional_eligibility import FunctionalRestrictions

VALID_SEXES = {
    "male",
    "female",
    "other",
    "prefer_not_to_say",
}

VALID_GOALS = {
    "general_fitness",
    "weight_management",
    "strength",
    "endurance",
}

VALID_LIMITATIONS = {
    "none",
    "knee",
    "hip",
    "shoulder",
    "wrist",
    "back",
    "ankle",
}


@dataclass
class UserProfile:
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    fitness_level: int
    activity_level: int
    goal: str
    workout_time_min: int
    limitations: list[str] = field(default_factory=list)
    user_id: str | None = None
    functional_restrictions: FunctionalRestrictions = field(
        default_factory=FunctionalRestrictions
    )
    @property
    def bmi(self) -> float:

        height_m = self.height_cm / 100

        if height_m <= 0:
            raise ValueError(
                "Height must be greater than zero."
            )

        return self.weight_kg / (height_m ** 2)

    def normalize(self):

        self.sex = self.sex.strip().lower()

        self.goal = self.goal.strip().lower()

        self.limitations = [
            limitation.strip().lower()
            for limitation in self.limitations
        ]

    def validate(self):

        self.normalize()

        errors = []

        # ----------------------------------------------------
        # AGE
        # ----------------------------------------------------

        if not isinstance(self.age, int):
            errors.append(
                "Age must be an integer."
            )

        elif self.age < 10:
            errors.append(
                "This version of the system is designed "
                "for adults aged 10 or older."
            )

        elif self.age > 100:
            errors.append(
                "Age must be 100 or below."
            )

        # ----------------------------------------------------
        # SEX
        # ----------------------------------------------------

        if self.sex not in VALID_SEXES:

            errors.append(
                f"Invalid sex value: {self.sex}"
            )

        # ----------------------------------------------------
        # HEIGHT
        # ----------------------------------------------------

        if self.height_cm <= 0:

            errors.append(
                "Height must be greater than zero."
            )

        elif not 100 <= self.height_cm <= 250:

            errors.append(
                "Height must be between 100 and 250 cm."
            )

        # ----------------------------------------------------
        # WEIGHT
        # ----------------------------------------------------

        if self.weight_kg <= 0:

            errors.append(
                "Weight must be greater than zero."
            )

        elif not 30 <= self.weight_kg <= 300:

            errors.append(
                "Weight must be between 30 and 300 kg."
            )

        # ----------------------------------------------------
        # FITNESS
        # ----------------------------------------------------

        if self.fitness_level not in range(1, 6):

            errors.append(
                "Fitness level must be an integer from 1 to 5."
            )

        # ----------------------------------------------------
        # ACTIVITY
        # ----------------------------------------------------

        if self.activity_level not in range(1, 6):

            errors.append(
                "Activity level must be an integer from 1 to 5."
            )

        # ----------------------------------------------------
        # GOAL
        # ----------------------------------------------------

        if self.goal not in VALID_GOALS:

            errors.append(
                f"Invalid goal: {self.goal}"
            )

        # ----------------------------------------------------
        # WORKOUT TIME
        # ----------------------------------------------------

        if not isinstance(
            self.workout_time_min,
            int,
        ):

            errors.append(
                "Workout time must be an integer."
            )

        elif not 10 <= self.workout_time_min <= 120:

            errors.append(
                "Workout time must be between "
                "10 and 120 minutes."
            )

        # ----------------------------------------------------
        # LIMITATIONS
        # ----------------------------------------------------

        invalid_limitations = [
            x
            for x in self.limitations
            if x not in VALID_LIMITATIONS
        ]

        if invalid_limitations:

            errors.append(
                "Invalid limitations: "
                + ", ".join(invalid_limitations)
            )

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        if errors:

            raise ValueError(
                "\n".join(
                    f"- {error}"
                    for error in errors
                )
            )

        return True
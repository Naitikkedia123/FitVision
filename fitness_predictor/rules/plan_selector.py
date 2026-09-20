from dataclasses import dataclass


@dataclass(frozen=True)
class PlanConfig:

    fitness_category: str

    min_difficulty: int
    max_difficulty: int

    intensity: str

    max_exercises: int


FITNESS_CONFIG = {

    1: PlanConfig(
        fitness_category="beginner",
        min_difficulty=1,
        max_difficulty=1,
        intensity="low",
        max_exercises=3,
    ),

    2: PlanConfig(
        fitness_category="beginner",
        min_difficulty=1,
        max_difficulty=2,
        intensity="low",
        max_exercises=4,
    ),

    3: PlanConfig(
        fitness_category="intermediate",
        min_difficulty=2,
        max_difficulty=3,
        intensity="moderate",
        max_exercises=5,
    ),

    4: PlanConfig(
        fitness_category="advanced",
        min_difficulty=2,
        max_difficulty=4,
        intensity="moderate",
        max_exercises=5,
    ),

    5: PlanConfig(
        fitness_category="advanced",
        min_difficulty=3,
        max_difficulty=4,
        intensity="moderate",
        max_exercises=6,
    ),
}


def get_plan_config(user):

    if user.fitness_level not in FITNESS_CONFIG:

        raise ValueError(
            "Invalid fitness level."
        )

    config = FITNESS_CONFIG[
        user.fitness_level
    ]

    # Activity level should not automatically
    # make a workout "high intensity".
    #
    # It is a separate input that we will use
    # later in the dosage model.

    return config


def get_fitness_category(
    fitness_level: int,
) -> str:

    return FITNESS_CONFIG[
        fitness_level
    ].fitness_category


def get_difficulty_range(
    fitness_level: int,
):

    config = FITNESS_CONFIG[
        fitness_level
    ]

    return (
        config.min_difficulty,
        config.max_difficulty,
    )


def get_intensity(
    fitness_level: int,
    activity_level: int,
) -> str:

    # Conservative baseline.
    #
    # Activity level should NOT by itself
    # force a high-intensity prescription.

    if fitness_level <= 2:
        return "low"

    if fitness_level == 3:
        return "moderate"

    if fitness_level >= 4:
        return "moderate"

    return "low"


def get_plan_type(user) -> str:

    category = get_fitness_category(
        user.fitness_level
    )

    if category == "beginner":

        if user.activity_level <= 2:
            return "beginner_foundation"

        return "beginner_active"

    if category == "intermediate":
        return "intermediate"

    return "advanced"
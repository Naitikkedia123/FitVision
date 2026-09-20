from dataclasses import dataclass
from typing import Literal

import math
import random


MeasurementType = Literal["reps", "time"]


@dataclass(frozen=True)
class SyntheticDosageTarget:
    sets: float
    reps: float | None = None
    duration_seconds: float | None = None


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def _bmi_factor(bmi: float) -> float:
    """
    Mild synthetic effect of BMI on exercise capacity.

    This is intentionally small so BMI does not dominate fitness/activity.
    """
    if bmi < 18.5:
        return -0.05

    if bmi < 25:
        return 0.05

    if bmi < 30:
        return 0.0

    return -0.08


def _age_factor(age: int) -> float:
    """
    Mild synthetic age adjustment.

    This is a prototype data-generation assumption, not a
    medically validated relationship.
    """
    if age <= 30:
        return 0.10

    if age <= 40:
        return 0.05

    if age <= 50:
        return 0.0

    if age <= 60:
        return -0.08

    return -0.15


def _goal_factor(goal: str) -> float:
    """
    Synthetic influence of workout goal.

    Supported goals:
        general_fitness
        endurance
        strength
    """

    factors = {
        "general_fitness": 0.00,
        "endurance": 0.12,
        "strength": 0.08,
    }

    return factors.get(goal, 0.0)


def generate_synthetic_target(
    *,
    age: int,
    height_cm: float,
    weight_kg: float,
    fitness_level: int,
    activity_level: int,
    workout_time_min: int,
    goal: str,
    individual_ability: float,
    exercise_difficulty: int,
    impact_level: int,
    knee_flexion_level: int,
    hip_load_level: int,
    shoulder_overhead_required: bool,
    wrist_weight_bearing: bool,
    back_load_level: int,
    ankle_load_level: int,
    floor_required: bool,
    single_leg: bool,
    measurement_type: MeasurementType,
    rng: random.Random,
) -> SyntheticDosageTarget:

    if measurement_type not in {"reps", "time"}:
        raise ValueError(
            f"Unsupported measurement_type: {measurement_type!r}"
        )

    if not 18 <= age <= 100:
        raise ValueError("age must be between 18 and 100.")

    if height_cm <= 0:
        raise ValueError("height_cm must be greater than 0.")

    if weight_kg <= 0:
        raise ValueError("weight_kg must be greater than 0.")

    if not 1 <= fitness_level <= 5:
        raise ValueError("fitness_level must be between 1 and 5.")

    if not 1 <= activity_level <= 5:
        raise ValueError("activity_level must be between 1 and 5.")

    if workout_time_min < 10:
        raise ValueError("workout_time_min must be at least 10.")

    if individual_ability <= 0:
        raise ValueError(
            "individual_ability must be greater than 0."
        )

    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2)

    # ---------------------------------------------------------
    # 1. Personal capacity
    # ---------------------------------------------------------

    fitness_component = fitness_level * 0.90
    activity_component = activity_level * 0.55

    workout_component = (
        min(workout_time_min, 60) / 10.0
    ) * 0.18

    age_component = _age_factor(age)
    bmi_component = _bmi_factor(bmi)
    goal_component = _goal_factor(goal)

    personal_capacity = (
        fitness_component
        + activity_component
        + workout_component
        + age_component
        + bmi_component
        + goal_component
    )

    # Persistent user-to-user variation.
    personal_capacity *= individual_ability

    # ---------------------------------------------------------
    # 2. Exercise demand
    # ---------------------------------------------------------

    exercise_demand = (
        exercise_difficulty * 0.55
        + impact_level * 0.25
        + knee_flexion_level * 0.20
        + hip_load_level * 0.20
        + back_load_level * 0.18
        + ankle_load_level * 0.15
    )

    if shoulder_overhead_required:
        exercise_demand += 0.15

    if wrist_weight_bearing:
        exercise_demand += 0.15

    if floor_required:
        exercise_demand += 0.05

    if single_leg:
        exercise_demand += 0.10

    # ---------------------------------------------------------
    # 3. Effective capacity for this specific exercise
    # ---------------------------------------------------------

    effective_capacity = personal_capacity - exercise_demand

    effective_capacity = _clamp(
        effective_capacity,
        0.5,
        8.0,
    )

    # ---------------------------------------------------------
    # 4. Controlled individual variation
    # ---------------------------------------------------------

    noise_multiplier = rng.gauss(
        mu=1.0,
        sigma=0.04,
    )

    noise_multiplier = _clamp(
        noise_multiplier,
        0.90,
        1.10,
    )

    effective_capacity *= noise_multiplier

    # ---------------------------------------------------------
    # 5. Generate target
    # ---------------------------------------------------------

    if measurement_type == "reps":

        reps = 5.0 + effective_capacity * 1.65

        sets = 0.9 + effective_capacity / 2.7

        return SyntheticDosageTarget(
            sets=round(sets, 3),
            reps=round(reps, 3),
        )

    duration_seconds = (
        12.0
        + effective_capacity * 6.5
    )

    sets = 0.9 + effective_capacity / 2.7

    return SyntheticDosageTarget(
        sets=round(sets, 3),
        duration_seconds=round(duration_seconds, 3),
    )
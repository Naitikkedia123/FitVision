from collections import defaultdict
from typing import Any

from services.week1_dosage_service import Week1DosageService

CATEGORY_ORDER = [
    "cardio",
    "lower_body",
    "upper_body",
    "core",
]


def group_by_category(
    exercises: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Group eligible exercises by exercise category.
    """

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for exercise in exercises:
        category = exercise.get("category")

        if category in CATEGORY_ORDER:
            grouped[category].append(exercise)

    # Convert defaultdict into a normal dictionary containing
    # all supported categories.
    return {
        category: grouped.get(category, [])
        for category in CATEGORY_ORDER
    }


def get_max_exercises(
    workout_time_min: int,
    plan_max_exercises: int,
) -> int:
    """
    Determine how many different exercises can fit into one
    workout based only on workout duration and the fitness
    plan's maximum.

    This does NOT determine sets, reps, or duration.
    """

    if workout_time_min < 10:
        raise ValueError(
            "workout_time_min must be at least 10 minutes."
        )

    if plan_max_exercises < 1:
        raise ValueError(
            "plan_max_exercises must be at least 1."
        )

    if workout_time_min <= 15:
        requested = 3
    elif workout_time_min <= 25:
        requested = 4
    elif workout_time_min <= 40:
        requested = 5
    else:
        requested = 6

    return min(requested, plan_max_exercises)


def select_balanced_exercises(
    exercises: list[dict[str, Any]],
    workout_time_min: int,
    plan_max_exercises: int,
    rotation_offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Select a balanced set of exercises from the eligible pool.

    Selection happens in two stages:

    1. Try to select one exercise from each available category.
    2. If more exercises are allowed, fill remaining slots by
       rotating through the categories.

    No dosage is assigned here.
    """

    if not exercises:
        raise ValueError(
            "Cannot select exercises from an empty pool."
        )

    max_exercises = get_max_exercises(
        workout_time_min=workout_time_min,
        plan_max_exercises=plan_max_exercises,
    )

    grouped = group_by_category(exercises)

    available_categories = [
        category
        for category in CATEGORY_ORDER
        if grouped[category]
    ]

    if not available_categories:
        raise RuntimeError(
            "No supported exercise categories are available."
        )

    selected: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    # ---------------------------------------------------------
    # Stage 1:
    # Try to select one exercise from every available category.
    # ---------------------------------------------------------

    for category in available_categories:
        candidates = grouped[category]

        index = rotation_offset % len(candidates)
        exercise = candidates[index]

        if exercise["id"] not in used_ids:
            selected.append(exercise)
            used_ids.add(exercise["id"])

        if len(selected) >= max_exercises:
            return selected

    # ---------------------------------------------------------
    # Stage 2:
    # Fill remaining slots while rotating through categories.
    # ---------------------------------------------------------

    category_index = rotation_offset

    while len(selected) < max_exercises:
        added = False

        for _ in range(len(available_categories)):
            category = available_categories[
                category_index % len(available_categories)
            ]
            category_index += 1

            candidates = grouped[category]

            for offset in range(len(candidates)):
                index = (
                    rotation_offset + offset
                ) % len(candidates)

                exercise = candidates[index]

                if exercise["id"] in used_ids:
                    continue

                selected.append(exercise)
                used_ids.add(exercise["id"])
                added = True
                break

            if len(selected) >= max_exercises:
                break

        # Every candidate has already been used.
        if not added:
            break

    return selected


def organize_week_one(
    eligible_exercises: list[dict[str, Any]],
    workout_time_min: int,
    plan_max_exercises: int,
) -> list[dict[str, Any]]:
    """
    Create the Week 1 exercise set.

    This is intentionally only exercise organization.

    There are NO:
        - sets
        - reps
        - target durations
        - intensity prescriptions
    """

    return select_balanced_exercises(
        exercises=eligible_exercises,
        workout_time_min=workout_time_min,
        plan_max_exercises=plan_max_exercises,
        rotation_offset=0,
    )

def generate_week_one_plan(
    user,
    eligible_exercises,
    total_exercises,
):
    """
    Generate Week 1 by:
    1. Selecting the balanced Week 1 exercises.
    2. Predicting and validating dosage for those exercises.
    """

    selected_exercises = select_balanced_exercises(
        eligible_exercises,
        user.workout_time_min,
        total_exercises,
        total_exercises,
    )

    dosage_service = Week1DosageService()
    dosages = dosage_service.generate(
        user,
        selected_exercises,
    )

    dosage_by_exercise_id = {
        dosage.exercise_id: dosage
        for dosage in dosages
    }

    week_one_plan = []

    for exercise in selected_exercises:
        dosage = dosage_by_exercise_id[exercise["id"]]

        week_one_plan.append(
            {
                **exercise,
                "sets": dosage.sets,
                "reps": dosage.reps,
                "duration_seconds": dosage.duration_seconds,
            }
        )

    return week_one_plan
from collections import defaultdict
from typing import Any


CATEGORY_ORDER = [
    "cardio",
    "lower_body",
    "upper_body",
    "core",
]


# Fraction of exercises we try to RETAIN from the previous week.
# The rest will be swapped with another exercise from the same category.
RETENTION_RATE = {
    1: 1.00,   # Week 1 = baseline
    2: 0.50,   # Week 2 = ~50% retain
    3: 0.25,   # Week 3 = ~25% retain
    4: 0.40,   # Week 4 = ~40% retain
}


def group_by_category(
    exercises: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Group eligible exercises by category.
    """

    grouped: dict[str, list[dict[str, Any]]] = {
        category: []
        for category in CATEGORY_ORDER
    }

    for exercise in exercises:
        category = exercise.get("category")

        if category in grouped:
            grouped[category].append(exercise)

    return grouped


def _ordered_candidates(
    candidates: list[dict[str, Any]],
    week_number: int,
    recent_ids: set[str],
    selected_ids: set[str],
    exposure_counts: dict[str, int] | None = None,
    activity_level: int = 3,
) -> list[dict[str, Any]]:
    """
    Order candidates for weekly selection.

    Priority:
    1. Not already selected this week.
    2. Lower total exposure.
    3. Avoid recently used exercises.
    4. Rotate deterministic ordering across weeks.

    Lower exposure is preferred because the scheduler should
    distribute exercise usage rather than repeatedly selecting
    the same exercise.
    """

    available = [
        exercise
        for exercise in candidates
        if exercise["id"] not in selected_ids
    ]

    if not available:
        return []

    exposure_counts = exposure_counts or {}

    def sort_key(exercise: dict[str, Any]) -> tuple:
        exercise_id = exercise["id"]

        exposure = exposure_counts.get(
            exercise_id,
            0,
        )

        recent_penalty = (
            activity_level
            if exercise_id in recent_ids
            else 0
        )

        rotation_offset = (
            week_number - 1
        ) % max(len(available), 1)

        return (
            exposure + recent_penalty,
            recent_penalty,
            rotation_offset,
            exercise_id,
        )

    return sorted(
        available,
        key=sort_key,
    )


def _select_retained_exercise(
    candidates: list[dict[str, Any]],
    previous_ids: set[str],
    selected_ids: set[str],
) -> dict[str, Any] | None:
    """
    Select an exercise from the previous week if possible.
    """

    for exercise in candidates:
        if (
            exercise["id"] in previous_ids
            and exercise["id"] not in selected_ids
        ):
            return exercise

    return None


def _select_swapped_exercise(
    candidates: list[dict[str, Any]],
    previous_ids: set[str],
    recent_ids: set[str],
    selected_ids: set[str],
    week_number: int,
    exposure_counts: dict[str, int] | None = None,
    activity_level: int = 3,
) -> dict[str, Any] | None:
    """
    Select a replacement from the SAME category.

    Preference:
    1. Not used in the previous week.
    2. Lower total exposure.
    3. Not recently used.
    4. Not already selected this week.
    """

    ordered = _ordered_candidates(
        candidates=candidates,
        week_number=week_number,
        recent_ids=recent_ids,
        selected_ids=selected_ids,
        exposure_counts=exposure_counts,
        activity_level=activity_level,
    )

    # First preference:
    # something not present in previous week.
    new_candidates = [
        exercise
        for exercise in ordered
        if exercise["id"] not in previous_ids
    ]

    if new_candidates:
        return new_candidates[0]

    # Fallback:
    # any unused candidate.
    if ordered:
        return ordered[0]

    return None


def _calculate_retained_count(
    total_exercises: int,
    week_number: int,
) -> int:
    """
    Calculate how many exercises to retain from the previous week.
    """

    if week_number == 1:
        return total_exercises

    retention_rate = RETENTION_RATE[week_number]

    retained = round(
        total_exercises * retention_rate
    )

    # For any multi-exercise workout, ensure that we actually
    # perform some swapping in Weeks 2-4 when alternatives exist.
    if total_exercises > 1:
        retained = min(
            retained,
            total_exercises - 1,
        )

    return max(retained, 0)


def _category_order_for_week(
    available_categories: list[str],
    week_number: int,
) -> list[str]:
    """
    Rotate category priority across weeks.

    This influences which category receives extra exercise slots.
    """

    if not available_categories:
        return []

    offset = (
        week_number - 1
    ) % len(available_categories)

    return (
        available_categories[offset:]
        + available_categories[:offset]
    )


def _rotation_window_days(
    activity_level: int,
) -> int:
    """
    Determine how many consecutive days an exercise set remains
    active before rotation.

    Activity 1-2 → 7 days
    Activity 3   → 4 days
    Activity 4-5 → 1 day
    """

    if not isinstance(activity_level, int):
        raise TypeError(
            "activity_level must be an integer."
        )

    if not 1 <= activity_level <= 5:
        raise ValueError(
            "activity_level must be between 1 and 5."
        )

    if activity_level <= 2:
        return 7

    if activity_level == 3:
        return 4

    return 1


def _select_daily_rotation_exercises(
    eligible_exercises: list[dict[str, Any]],
    total_exercises: int,
    exposure_counts: dict[str, int],
    recent_exercises: list[dict[str, Any]],
    activity_level: int,
) -> list[dict[str, Any]]:
    """
    Select exercises for a new daily rotation window.

    Unlike the original weekly selector, this function does NOT
    force one exercise from every category.

    That is intentional.

    When a category has very few exercises, repeatedly forcing
    that category can make one exercise dominate the entire
    28-day schedule.

    Instead, selection is driven primarily by:
    1. total exposure,
    2. recent usage,
    3. category distribution.

    Lower-exposure exercises are preferred.
    """

    if not eligible_exercises:
        raise ValueError(
            "eligible_exercises cannot be empty."
        )

    if total_exercises < 1:
        raise ValueError(
            "total_exercises must be at least 1."
        )

    target_count = min(
        total_exercises,
        len(eligible_exercises),
    )

    recent_ids = {
        exercise["id"]
        for exercise in recent_exercises
    }

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    category_usage: defaultdict[str, int] = defaultdict(int)

    while len(selected) < target_count:

        candidates = [
            exercise
            for exercise in eligible_exercises
            if exercise["id"] not in selected_ids
        ]

        if not candidates:
            break

        def score(
            exercise: dict[str, Any],
        ) -> tuple:
            exercise_id = exercise["id"]
            category = exercise.get(
                "category",
                "unknown",
            )

            exposure = exposure_counts.get(
                exercise_id,
                0,
            )

            recent_penalty = (
                activity_level
                if exercise_id in recent_ids
                else 0
            )

            category_usage_penalty = (
                category_usage[category]
            )

            return (
                exposure + recent_penalty,
                category_usage_penalty,
                recent_penalty,
                exposure,
                exercise_id,
            )

        best = min(
            candidates,
            key=score,
        )

        selected.append(best)
        selected_ids.add(best["id"])

        category_usage[
            best.get("category", "unknown")
        ] += 1

    if len(selected) < target_count:
        raise RuntimeError(
            f"Unable to generate {target_count} daily exercises."
        )

    return selected


def generate_week(
    eligible_exercises: list[dict[str, Any]],
    total_exercises: int,
    week_number: int,
    previous_week: list[dict[str, Any]] | None = None,
    recent_exercises: list[dict[str, Any]] | None = None,
    exposure_counts: dict[str, int] | None = None,
    activity_level: int = 3,
) -> list[dict[str, Any]]:
    """
    Generate one week's exercise skeleton.

    Rules:
    1. Use only eligible exercises.
    2. Keep category balance for the base weekly schedule.
    3. Retain some exercises from the previous week.
    4. Swap other exercises within the same category.
    5. Prefer lower-exposure and less recently used exercises.
    6. ALWAYS fill the requested number of exercise slots when
       the eligible pool contains enough exercises.
    7. Reuse an eligible exercise as a final fallback if needed.
    """

    if not eligible_exercises:
        raise ValueError(
            "eligible_exercises cannot be empty."
        )

    if total_exercises < 1:
        raise ValueError(
            "total_exercises must be at least 1."
        )

    if week_number not in {1, 2, 3, 4}:
        raise ValueError(
            "week_number must be between 1 and 4."
        )

    grouped = group_by_category(
        eligible_exercises
    )

    available_categories = [
        category
        for category in CATEGORY_ORDER
        if grouped[category]
    ]

    if not available_categories:
        raise RuntimeError(
            "No supported exercise categories are available."
        )

    target_count = min(
        total_exercises,
        len(eligible_exercises),
    )

    previous_week = previous_week or []
    recent_exercises = recent_exercises or []
    exposure_counts = exposure_counts or {}

    previous_ids = {
        exercise["id"]
        for exercise in previous_week
    }

    recent_ids = {
        exercise["id"]
        for exercise in recent_exercises
    }

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    # ---------------------------------------------------------
    # WEEK 1
    # ---------------------------------------------------------

    if week_number == 1:
        category_order = _category_order_for_week(
            available_categories,
            week_number,
        )

        # First give every available category one slot.
        for category in category_order:
            if len(selected) >= target_count:
                break

            ordered = _ordered_candidates(
                candidates=grouped[category],
                week_number=week_number,
                recent_ids=set(),
                selected_ids=selected_ids,
                exposure_counts=exposure_counts,
                activity_level=activity_level,
            )

            if ordered:
                exercise = ordered[0]
                selected.append(exercise)
                selected_ids.add(exercise["id"])

        # Fill remaining slots.
        category_index = 0

        while len(selected) < target_count:
            category = category_order[
                category_index
                % len(category_order)
            ]

            category_index += 1

            ordered = _ordered_candidates(
                candidates=grouped[category],
                week_number=week_number,
                recent_ids=set(),
                selected_ids=selected_ids,
                exposure_counts=exposure_counts,
                activity_level=activity_level,
            )

            if ordered:
                exercise = ordered[0]
                selected.append(exercise)
                selected_ids.add(exercise["id"])

            if (
                category_index
                > len(category_order) * 10
            ):
                break

        return selected

    # ---------------------------------------------------------
    # WEEKS 2-4
    # ---------------------------------------------------------

    retained_target = _calculate_retained_count(
        target_count,
        week_number,
    )

    category_order = _category_order_for_week(
        available_categories,
        week_number,
    )

    # Build category assignments.
    category_assignments: list[str] = []

    # First pass: one slot per category.
    for category in category_order:
        if len(category_assignments) >= target_count:
            break

        category_assignments.append(category)

    # Extra slots rotate through categories.
    category_index = 0

    while len(category_assignments) < target_count:
        category_assignments.append(
            category_order[
                category_index
                % len(category_order)
            ]
        )

        category_index += 1

    # ---------------------------------------------------------
    # First pass: retention + preferred swaps
    # ---------------------------------------------------------

    retained_count = 0

    for category in category_assignments:
        if len(selected) >= target_count:
            break

        candidates = grouped[category]

        if retained_count < retained_target:
            retained = _select_retained_exercise(
                candidates=candidates,
                previous_ids=previous_ids,
                selected_ids=selected_ids,
            )

            if retained is not None:
                selected.append(retained)
                selected_ids.add(retained["id"])
                retained_count += 1
                continue

        swapped = _select_swapped_exercise(
            candidates=candidates,
            previous_ids=previous_ids,
            recent_ids=recent_ids,
            selected_ids=selected_ids,
            week_number=week_number,
            exposure_counts=exposure_counts,
            activity_level=activity_level,
        )

        if swapped is not None:
            selected.append(swapped)
            selected_ids.add(swapped["id"])

    # ---------------------------------------------------------
    # GUARANTEE TARGET COUNT
    #
    # If recent-exercise avoidance caused us to have fewer
    # exercises than requested, relax the recent-history
    # restriction and choose any remaining eligible exercises.
    # ---------------------------------------------------------

    if len(selected) < target_count:

        remaining = [
            exercise
            for exercise in eligible_exercises
            if exercise["id"] not in selected_ids
        ]

        remaining = sorted(
            remaining,
            key=lambda exercise: (
                exposure_counts.get(
                    exercise["id"],
                    0,
                ),
                exercise["id"],
            ),
        )

        for exercise in remaining:
            selected.append(exercise)
            selected_ids.add(exercise["id"])

            if len(selected) >= target_count:
                break

    # ---------------------------------------------------------
    # FINAL FALLBACK
    #
    # If there are not enough UNIQUE exercises to fill the
    # requested slots, reuse eligible exercises.
    # ---------------------------------------------------------

    if len(selected) < target_count:

        for category in category_order:
            if len(selected) >= target_count:
                break

            candidates = grouped[category]

            if not candidates:
                continue

            ordered = _ordered_candidates(
                candidates=candidates,
                week_number=week_number,
                recent_ids=recent_ids,
                selected_ids=set(),
                exposure_counts=exposure_counts,
                activity_level=activity_level,
            )

            for exercise in ordered:
                selected.append(exercise)

                if len(selected) >= target_count:
                    break

    if len(selected) < target_count:
        raise RuntimeError(
            f"Unable to generate {target_count} exercises "
            f"for Week {week_number}."
        )

    return selected


def _rotate_week_daily(
    *,
    eligible_exercises: list[dict[str, Any]],
    base_exercises: list[dict[str, Any]],
    week_number: int,
    activity_level: int,
    total_exercises: int,
    exposure_counts: dict[str, int],
    recent_exercises: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    """
    Expand one weekly exercise set into seven daily exercise sets.

    Rotation frequency depends on activity level:

    Activity 1-2 → 7-day window
    Activity 3   → 4-day window
    Activity 4-5 → daily rotation

    Exposure counts and recent usage are tracked across the
    entire 28-day schedule.
    """

    if not base_exercises:
        raise ValueError(
            "base_exercises cannot be empty."
        )

    rotation_window = _rotation_window_days(
        activity_level
    )

    daily_schedule: dict[
        int,
        list[dict[str, Any]]
    ] = {}

    current_exercises = list(
        base_exercises
    )

    for day_number in range(1, 8):

        # Start a new rotation window.
        if (
            day_number > 1
            and (day_number - 1)
            % rotation_window == 0
        ):
            current_exercises = (
                _select_daily_rotation_exercises(
                    eligible_exercises=eligible_exercises,
                    total_exercises=total_exercises,
                    exposure_counts=exposure_counts,
                    recent_exercises=recent_exercises,
                    activity_level=activity_level,
                )
            )

        daily_schedule[day_number] = list(
            current_exercises
        )

        # Every scheduled appearance counts as an exposure.
        for exercise in current_exercises:
            exercise_id = exercise["id"]

            exposure_counts[exercise_id] = (
                exposure_counts.get(
                    exercise_id,
                    0,
                )
                + 1
            )

        # Add today's exercises to recent history.
        recent_exercises.extend(
            current_exercises
        )

        # Keep the recent history bounded.
        recent_limit = max(
            total_exercises * 2,
            1,
        )

        if len(recent_exercises) > recent_limit:
            del recent_exercises[
                :-recent_limit
            ]

    return daily_schedule


def generate_four_week_schedule(
    eligible_exercises: list[dict[str, Any]],
    total_exercises: int,
    activity_level: int = 3,
) -> dict[
    int,
    dict[int, list[dict[str, Any]]]
]:
    """
    Generate the four-week exercise skeleton.

    Output structure:

        {
            week_number: {
                day_number: [exercise, ...]
            }
        }

    The scheduler tracks exposure across all 28 days.
    """

    if not eligible_exercises:
        raise ValueError(
            "eligible_exercises cannot be empty."
        )

    if total_exercises < 1:
        raise ValueError(
            "total_exercises must be at least 1."
        )

    if not isinstance(activity_level, int):
        raise TypeError(
            "activity_level must be an integer."
        )

    if not 1 <= activity_level <= 5:
        raise ValueError(
            "activity_level must be between 1 and 5."
        )

    daily_schedule: dict[
        int,
        dict[int, list[dict[str, Any]]]
    ] = {}

    # These persist across the entire 28-day plan.
    exposure_counts: dict[str, int] = {}
    recent_exercises: list[dict[str, Any]] = []

    previous_week: list[dict[str, Any]] = []

    for week_number in range(1, 5):

        # Generate a weekly base using all exposure information
        # accumulated from previous days.
        current_week = generate_week(
            eligible_exercises=eligible_exercises,
            total_exercises=total_exercises,
            week_number=week_number,
            previous_week=previous_week,
            recent_exercises=recent_exercises,
            exposure_counts=exposure_counts,
            activity_level=activity_level,
        )

        if not current_week:
            raise RuntimeError(
                f"Unable to generate Week {week_number}."
            )

        # Expand the weekly base into daily workouts.
        daily_schedule[week_number] = (
            _rotate_week_daily(
                eligible_exercises=eligible_exercises,
                base_exercises=current_week,
                week_number=week_number,
                activity_level=activity_level,
                total_exercises=total_exercises,
                exposure_counts=exposure_counts,
                recent_exercises=recent_exercises,
            )
        )

        # The final day of this week becomes the previous-week
        # reference for Week 2/3/4.
        previous_week = list(
            daily_schedule[week_number][7]
        )

    return daily_schedule


def expand_weekly_schedule_to_daily(
    weekly_schedule: dict[
        int,
        list[dict]
    ],
) -> dict[
    int,
    dict[int, list[dict]]
]:
    """
    Backward-compatible helper.

    Convert:

        {week: [exercises]}

    into:

        {
            week: {
                day_of_week: [exercises],
                ...
            }
        }

    The new scheduler does not use this helper internally because
    activity-aware rotation is now handled by generate_four_week_schedule().
    """

    if not isinstance(weekly_schedule, dict):
        raise TypeError(
            "weekly_schedule must be a dictionary."
        )

    expanded_schedule: dict[
        int,
        dict[int, list[dict]]
    ] = {}

    for week_number, exercises in weekly_schedule.items():

        if not isinstance(week_number, int):
            raise TypeError(
                "week_number must be an integer."
            )

        if not isinstance(exercises, list):
            raise TypeError(
                f"Exercises for week {week_number} "
                "must be a list."
            )

        expanded_schedule[week_number] = {}

        for day_number in range(1, 8):
            expanded_schedule[
                week_number
            ][day_number] = list(exercises)

    return expanded_schedule
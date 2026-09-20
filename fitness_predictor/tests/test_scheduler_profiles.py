from models.user_profile import UserProfile
from rules.eligibility import EligibilityService
from rules.plan_selector import get_plan_config
from planning.plan_generator import organize_week_one
from planning.weekly_scheduler import generate_four_week_schedule
from services.auth_service import AuthService
from rules.functional_eligibility import FunctionalRestrictions


def build_profile(
    fitness_level: int,
    activity_level: int,
    workout_time_min: int,
    goal: str = "general_fitness",
    limitations: list[str] | None = None,
    functional_restrictions: FunctionalRestrictions | None = None,
) -> UserProfile:
    """
    Build a test user profile.

    We use a fake user_id here because this test is focused on
    planner behavior, not Supabase authentication.
    """

    return UserProfile(
        age=25,
        sex="male",
        height_cm=175,
        weight_kg=70,
        fitness_level=fitness_level,
        activity_level=activity_level,
        goal=goal,
        workout_time_min=workout_time_min,
        limitations=limitations or [],
        user_id="e560b49f-1255-490b-a74a-e89820cc5e82",
        functional_restrictions=(
            functional_restrictions
            or FunctionalRestrictions()
        ),
    )


def validate_profile(
    user: UserProfile,
) -> None:
    """
    Validate exercise selection and 4-week scheduling for one profile.
    """

    # Authenticate once so the exercise repository can read
    # the RLS-protected exercises table.
    auth = AuthService()

    auth.sign_in(
        "kedianaitik2006@gmail.com",
        "naitik123",
    )

    eligibility_service = EligibilityService()

    eligible = eligibility_service.get_eligible_exercises(
        user
    )

    config = get_plan_config(user)

    expected_max = min(
        {
            10: 3,
            15: 3,
            20: 4,
            25: 4,
            30: 5,
            40: 5,
            45: 6,
            60: 6,
        }.get(user.workout_time_min, 6),
        config.max_exercises,
    )

    print()
    print("=" * 60)
    print(
        f"Fitness={user.fitness_level}, "
        f"Activity={user.activity_level}, "
        f"Time={user.workout_time_min}, "
        f"Limitations={user.limitations}"
    )
    print("=" * 60)

    print("Eligible exercises:", len(eligible))

    if not eligible:
        raise AssertionError(
            "No eligible exercises were produced."
        )

    # ---------------------------------------------------------
    # Week 1
    # ---------------------------------------------------------

    week_one = organize_week_one(
        eligible_exercises=eligible,
        workout_time_min=user.workout_time_min,
        plan_max_exercises=config.max_exercises,
    )

    expected_week_one_count = min(
        expected_max,
        len(eligible),
    )

    if len(week_one) != expected_week_one_count:
        raise AssertionError(
            f"Week 1 expected {expected_week_one_count} "
            f"exercises, got {len(week_one)}."
        )

    # ---------------------------------------------------------
    # Difficulty validation
    # ---------------------------------------------------------

    plan_min_difficulty = config.min_difficulty
    plan_max_difficulty = config.max_difficulty

    for exercise in eligible:
        difficulty = exercise["difficulty"]

        if not (
            plan_min_difficulty
            <= difficulty
            <= plan_max_difficulty
        ):
            raise AssertionError(
                f"Exercise outside difficulty range: "
                f"{exercise['name']} "
                f"(difficulty={difficulty})"
            )

    # ---------------------------------------------------------
    # 4-week schedule
    # ---------------------------------------------------------

    schedule = generate_four_week_schedule(
        eligible_exercises=eligible,
        total_exercises=config.max_exercises,
    )

    if len(schedule) != 4:
        raise AssertionError(
            f"Expected 4 weeks, got {len(schedule)}."
        )

    for week_number, exercises in schedule.items():

        expected_count = min(
            config.max_exercises,
            len(eligible),
        )

        if len(exercises) != expected_count:
            raise AssertionError(
                f"Week {week_number}: expected "
                f"{expected_count} exercises, "
                f"got {len(exercises)}."
            )

        exercise_ids = [
            exercise["id"]
            for exercise in exercises
        ]

        if len(exercise_ids) != len(set(exercise_ids)):
            raise AssertionError(
                f"Week {week_number} contains duplicate "
                f"exercise IDs."
            )

        print(
            f"Week {week_number}: "
            f"{[(x['name'], x['category']) for x in exercises]}"
        )

    print("PROFILE PASSED ✅")


def main():
    """
    Test several representative user profiles.
    """

    profiles = [
        # Beginner + short workout
        build_profile(
            fitness_level=1,
            activity_level=1,
            workout_time_min=15,
        ),

        # Beginner/intermediate
        build_profile(
            fitness_level=2,
            activity_level=2,
            workout_time_min=20,
        ),

        # Intermediate
        build_profile(
            fitness_level=3,
            activity_level=3,
            workout_time_min=30,
        ),

        # Advanced
        build_profile(
            fitness_level=4,
            activity_level=4,
            workout_time_min=30,
        ),

        # Advanced + longer workout
        build_profile(
            fitness_level=5,
            activity_level=5,
            workout_time_min=45,
        ),
        # Advanced + functional restrictions
        build_profile(
            fitness_level=4,
            activity_level=4,
            workout_time_min=30,
            functional_restrictions=FunctionalRestrictions(
                avoid_overhead_shoulder=True,
                avoid_wrist_weight_bearing=True,
            ),
        ),
    ]

    for profile in profiles:
        validate_profile(profile)

    print()
    print("=" * 60)
    print("ALL PROFILE TESTS PASSED ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
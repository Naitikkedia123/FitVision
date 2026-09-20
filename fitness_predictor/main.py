from models.user_profile import UserProfile

from rules.plan_selector import (
    get_fitness_category,
    get_intensity,
    get_plan_type,
)

from rules.eligibility import (
    get_eligible_exercises,
)

from planning.plan_generator import (
    generate_workout,
)

from planning.workout_state import (
    WorkoutState,
)


def print_workout(workout):

    print("\n")
    print("=" * 60)

    print(
        f"WORKOUT #{workout['workout_number']}"
    )

    print(
        f"WEEK {workout['week']}"
    )

    print("=" * 60)

    if not workout["exercises"]:

        print(
            "No eligible exercises found."
        )

        return

    for exercise in workout["exercises"]:

        print(
            f"\n{exercise['exercise']}"
        )

        print(
            f"Category: "
            f"{exercise['category']}"
        )

        print(
            f"Measurement: "
            f"{exercise['measurement']}"
        )

        print(
            f"Sets: "
            f"{exercise['sets']}"
        )

        if "reps" in exercise:

            print(
                f"Reps: "
                f"{exercise['reps']}"
            )

        if "duration_sec" in exercise:

            print(
                f"Duration: "
                f"{exercise['duration_sec']} sec"
            )


def main():

    try:

        # ====================================================
        # USER PROFILE
        # ====================================================

        user = UserProfile(

            age=22,

            sex="male",

            height_cm=175,

            weight_kg=70,

            fitness_level=4,

            activity_level=4,

            goal="general_fitness",

            workout_time_min=30,

            limitations=[],
        )

        # ====================================================
        # VALIDATION
        # ====================================================

        user.validate()

        print("\nINPUT VALIDATION")
        print("-" * 60)

        print("Valid input ✓")

        # ====================================================
        # CLASSIFICATION
        # ====================================================

        fitness_category = (
            get_fitness_category(
                user.fitness_level
            )
        )

        intensity = get_intensity(
            user.fitness_level,
            user.activity_level,
        )

        plan_type = get_plan_type(
            user
        )

        print("\nUSER PROFILE")
        print("-" * 60)

        print("Age:", user.age)

        print(
            "BMI:",
            round(user.bmi, 2),
        )

        print(
            "Fitness Level:",
            user.fitness_level,
        )

        print(
            "Activity Level:",
            user.activity_level,
        )

        print(
            "Fitness Category:",
            fitness_category,
        )

        print(
            "Intensity:",
            intensity,
        )

        print(
            "Plan Type:",
            plan_type,
        )

        # ====================================================
        # ELIGIBILITY
        # ====================================================

        eligible_exercises = (
            get_eligible_exercises(
                user
            )
        )

        if not eligible_exercises:

            raise RuntimeError(
                "No suitable exercises were found "
                "for this user."
            )

        print(
            "\nELIGIBLE EXERCISES"
        )

        print("-" * 60)

        for exercise in eligible_exercises:

            print(
                f"- {exercise['name']}"
            )

        # ====================================================
        # WORKOUT STATE
        # ====================================================

        state = WorkoutState()

        # ====================================================
        # CURRENT WORKOUT
        # ====================================================

        workout = generate_workout(
            user,
            eligible_exercises,
            state.current_workout,
        )

        print_workout(workout)

        print(
            "\nSTATUS:",
            state.status,
        )

        # ====================================================
        # START
        # ====================================================

        if not state.start_workout():

            raise RuntimeError(
                "Workout could not be started."
            )

        print(
            "\nSTATUS:",
            state.status,
        )

        # ====================================================
        # SIMULATE TRAINER COMPLETION
        # ====================================================

        # In the real application, your existing
        # AI trainer will call this only after
        # every required set/exercise is completed.

        completed = (
            state.complete_workout()
        )

        if not completed:

            raise RuntimeError(
                "Workout could not be completed."
            )

        print(
            "\nWorkout completed:",
            completed,
        )

        print(
            "STATUS:",
            state.status,
        )

        # ====================================================
        # ADVANCE
        # ====================================================

        advanced = (
            state.advance_to_next_workout()
        )

        if not advanced:

            print(
                "\nPlan is complete or "
                "workout cannot advance."
            )

            return

        print(
            "\nMoved to workout:",
            state.current_workout,
        )

        print(
            "Current week:",
            state.current_week,
        )

        # ====================================================
        # NEXT WORKOUT
        # ====================================================

        next_workout = generate_workout(
            user,
            eligible_exercises,
            state.current_workout,
        )

        print_workout(next_workout)

    except ValueError as error:

        print(
            "\nINPUT ERROR:"
        )

        print(error)

    except RuntimeError as error:

        print(
            "\nPLAN ERROR:"
        )

        print(error)

    except Exception as error:

        # Unexpected programming/system error.
        # In production, log this instead of
        # exposing internal details to the user.

        print(
            "\nUNEXPECTED ERROR:"
        )

        print(
            "The system could not generate "
            "the workout."
        )

        print(
            f"Developer details: {error}"
        )


if __name__ == "__main__":
    main()
from models.user_profile import UserProfile
from services.auth_service import AuthService
from rules.eligibility import EligibilityService
from services.four_week_plan_service import FourWeekPlanService


def main():
    auth_service = AuthService()

    auth_service.sign_in(
        email="kedianaitik2006@gmail.com",
        password="naitik123",
    )

    user = UserProfile(
        age=20,
        sex="male",
        height_cm=175,
        weight_kg=70,
        fitness_level=4,
        activity_level=4,
        goal="general_fitness",
        workout_time_min=30,
        user_id="e560b49f-1255-490b-a74a-e89820cc5e82",
    )

    eligibility_service = EligibilityService()

    eligible_exercises = (
        eligibility_service.get_eligible_exercises(user)
    )

    service = FourWeekPlanService()

    plan = service.generate(
        user=user,
        eligible_exercises=eligible_exercises,
    )

    # ---------------------------------------------------------
    # Validate overall structure
    # ---------------------------------------------------------

    assert set(plan.keys()) == {1, 2, 3, 4}

    total_days = 0
    total_exercises = 0

    # ---------------------------------------------------------
    # Validate every week/day/exercise
    # ---------------------------------------------------------

    for week_number in range(1, 5):
        assert set(plan[week_number].keys()) == {
            1, 2, 3, 4, 5, 6, 7
        }

        for day_number in range(1, 8):
            day = plan[week_number][day_number]

            assert len(day) == 5

            total_days += 1
            total_exercises += len(day)

            for exercise in day:
                assert exercise["id"]
                assert exercise["sets"] > 0

                # Exposure tracking
                assert exercise["exposure_number"] >= 1

                if exercise["measurement_type"] == "reps":
                    assert exercise["reps"] is not None
                    assert exercise["duration_seconds"] is None

                elif exercise["measurement_type"] == "time":
                    assert exercise["reps"] is None
                    assert exercise["duration_seconds"] is not None

                else:
                    raise AssertionError(
                        f"Unsupported measurement type: "
                        f"{exercise['measurement_type']}"
                    )

    # ---------------------------------------------------------
    # Validate total schedule size
    # ---------------------------------------------------------

    assert total_days == 28
    assert total_exercises == 140

    # ---------------------------------------------------------
    # Validate exposure numbers
    # ---------------------------------------------------------

    exposures = {}

    for week_number in range(1, 5):
        for day_number in range(1, 8):
            for exercise in plan[week_number][day_number]:
                exercise_id = exercise["id"]
                exposure_number = exercise["exposure_number"]

                if exercise_id in exposures:
                    assert (
                        exposure_number
                        == exposures[exercise_id] + 1
                    )

                exposures[exercise_id] = exposure_number

    # ---------------------------------------------------------
    # Success output
    # ---------------------------------------------------------

    print(
        "FOUR WEEK DAILY PLAN + EXPOSURE "
        "PROGRESSION TEST PASSED ✅"
    )

    print(f"Total days: {total_days}")
    print(f"Total exercises: {total_exercises}")

    print("\nExercise exposure counts:")

    for exercise_id, exposure_number in sorted(
        exposures.items()
    ):
        print(
            f"- {exercise_id}: "
            f"{exposure_number} exposures"
        )

    print("\nGenerated Schedule:")

    for week_number in range(1, 5):
        print(f"\nWeek {week_number}:")

        for day_number in range(1, 8):
            day = plan[week_number][day_number]

            print(f"  Day {day_number}:")

            for exercise in day:
                if exercise["measurement_type"] == "reps":
                    dosage = (
                        f"{exercise['sets']} sets × "
                        f"{exercise['reps']} reps"
                    )
                else:
                    dosage = (
                        f"{exercise['sets']} sets × "
                        f"{exercise['duration_seconds']}s"
                    )

                print(
                    f"    - {exercise['id']}: "
                    f"{dosage}, "
                    f"exposure={exercise['exposure_number']}"
                )


if __name__ == "__main__":
    main()
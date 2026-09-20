from models.user_profile import UserProfile
from rules.eligibility import EligibilityService
from planning.plan_generator import generate_week_one_plan
from database.repositories.eligibility_repository import EligibilityRepository
from services.auth_service import AuthService

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
    )

    eligibility_service = EligibilityService()

    repository = EligibilityRepository()

    raw_exercises = repository.get_eligible_exercises(user.limitations)

    print(f"Repository exercises: {len(raw_exercises)}")

    for exercise in raw_exercises:
        print(
            f"- {exercise['id']} | "
            f"difficulty={exercise['difficulty']}"
        )

    eligible_exercises = eligibility_service.get_eligible_exercises(user)

    print(f"Final eligible exercises: {len(eligible_exercises)}")

    for exercise in eligible_exercises:
        print(f"- {exercise['id']}")

    plan = generate_week_one_plan(
        user=user,
        eligible_exercises=eligible_exercises,
        total_exercises=5,
    )

    assert len(plan) == 5

    for exercise in plan:
        assert exercise["id"]
        assert exercise["sets"] is not None

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

    print("WEEK ONE PLAN TEST PASSED ✅")

    print("\nGenerated Week 1:")
    for exercise in plan:
        print(
            f"- {exercise['id']}: "
            f"{exercise['sets']} sets, "
            f"reps={exercise['reps']}, "
            f"time={exercise['duration_seconds']}s"
        )


if __name__ == "__main__":
    main()
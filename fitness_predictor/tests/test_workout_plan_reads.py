from services.auth_service import AuthService
from database.repositories.workout_plan_repository import WorkoutPlanRepository


USER_ID = "e560b49f-1255-490b-a74a-e89820cc5e82"


def main():
    auth_service = AuthService()

    auth_service.sign_in(
        email="kedianaitik2006@gmail.com",
        password="naitik123",
    )

    repository = WorkoutPlanRepository()

    plan = repository.get_active_plan(
        user_id=USER_ID
    )

    if plan is None:
        raise AssertionError(
            "No active workout plan found."
        )

    print(
        "Active plan:",
        plan["id"],
    )

    days = repository.get_plan_days(
        plan_id=str(plan["id"])
    )

    assert len(days) == 28, (
        f"Expected 28 days, got {len(days)}"
    )

    print(
        "Saved days:",
        len(days),
    )

    first_day = days[0]

    exercises = repository.get_day_exercises(
        workout_day_id=str(first_day["id"])
    )

    assert len(exercises) == 5, (
        f"Expected 5 exercises on first day, "
        f"got {len(exercises)}"
    )

    print(
        "First day exercises:",
        len(exercises),
    )

    print(
        "WORKOUT PLAN READ TEST PASSED ✅"
    )


if __name__ == "__main__":
    main()
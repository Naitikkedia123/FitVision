from services.auth_service import AuthService
from database.repositories.workout_plan_repository import WorkoutPlanRepository


def main():
    auth_service = AuthService()

    auth_service.sign_in(
        email="kedianaitik2006@gmail.com",
        password="naitik123",
    )

    repository = WorkoutPlanRepository()

    plan = repository.create_plan(
        user_id="e560b49f-1255-490b-a74a-e89820cc5e82",
        start_date="2026-09-14",
        end_date="2026-10-11",
        total_days=28,
        status="active",
    )

    assert plan["user_id"] == "e560b49f-1255-490b-a74a-e89820cc5e82"
    assert plan["start_date"] == "2026-09-14"
    assert plan["end_date"] == "2026-10-11"
    assert plan["total_days"] == 28
    assert plan["status"] == "active"

    day = repository.create_day(
        plan_id=str(plan["id"]),
        day_number=1,
        week_number=1,
        workout_date="2026-09-14",
        status="available",
    )

    assert day["plan_id"] == plan["id"]
    assert day["day_number"] == 1
    assert day["week_number"] == 1
    assert day["workout_date"] == "2026-09-14"
    assert day["status"] == "available"

    print(f"Created day: {day['id']}")

    print("WORKOUT PLAN REPOSITORY TEST PASSED ✅")
    print(f"Created plan: {plan['id']}")

    rep_exercise = repository.create_exercise(
        workout_day_id=str(day["id"]),
        exercise_id="bodyweight_squat",
        order_index=1,
        sets=3,
        target_reps=12,
        target_duration_seconds=None,
    )

    assert rep_exercise["exercise_id"] == "bodyweight_squat"
    assert rep_exercise["sets"] == 3
    assert rep_exercise["target_reps"] == 12
    assert rep_exercise["target_duration_seconds"] is None
    assert rep_exercise["status"] == "pending"

    time_exercise = repository.create_exercise(
        workout_day_id=str(day["id"]),
        exercise_id="plank",
        order_index=2,
        sets=3,
        target_reps=None,
        target_duration_seconds=30,
    )

    assert time_exercise["exercise_id"] == "plank"
    assert time_exercise["sets"] == 3
    assert time_exercise["target_reps"] is None
    assert time_exercise["target_duration_seconds"] == 30
    assert time_exercise["status"] == "pending"

    print(f"Created rep exercise: {rep_exercise['id']}")
    print(f"Created time exercise: {time_exercise['id']}")

if __name__ == "__main__":
    main()
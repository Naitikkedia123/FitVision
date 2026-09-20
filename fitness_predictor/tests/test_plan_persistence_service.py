from datetime import date

from models.user_profile import UserProfile
from services.auth_service import AuthService
from rules.eligibility import EligibilityService
from services.four_week_plan_service import FourWeekPlanService
from services.plan_persistence_service import PlanPersistenceService


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

    plan_service = FourWeekPlanService()

    four_week_plan = plan_service.generate(
        user=user,
        eligible_exercises=eligible_exercises,
    )

    persistence_service = PlanPersistenceService()

    saved_plan = persistence_service.save_plan(
        user=user,
        four_week_plan=four_week_plan,
        start_date=date(2026, 9, 14),
    )

    assert saved_plan["user_id"] == user.user_id
    assert saved_plan["total_days"] == 28
    assert saved_plan["status"] == "active"

    assert len(saved_plan["days"]) == 28

    for day in saved_plan["days"]:
        assert day["plan_id"] == saved_plan["id"]
        assert day["day_number"] >= 1
        assert day["week_number"] in {1, 2, 3, 4}
        assert len(day["exercises"]) == 5

        for exercise in day["exercises"]:
            assert exercise["workout_day_id"] == day["id"]
            assert exercise["sets"] > 0
            assert exercise["status"] == "pending"

            if exercise["target_reps"] is not None:
                assert exercise["target_duration_seconds"] is None

            if exercise["target_duration_seconds"] is not None:
                assert exercise["target_reps"] is None

    print("PLAN PERSISTENCE SERVICE TEST PASSED ✅")
    print(f"Created plan: {saved_plan['id']}")
    print(f"Saved days: {len(saved_plan['days'])}")

    total_exercises = sum(
        len(day["exercises"])
        for day in saved_plan["days"]
    )

    print(f"Saved workout exercises: {total_exercises}")


if __name__ == "__main__":
    main()
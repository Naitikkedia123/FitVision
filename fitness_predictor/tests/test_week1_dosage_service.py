from models.user_profile import UserProfile
from services.week1_dosage_service import Week1DosageService


def main():
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

    exercises = [
        {
            "id": "bodyweight_squat",
            "measurement_type": "reps",
        },
        {
            "id": "plank",
            "measurement_type": "time",
        },
        {
            "id": "wall_push_up",
            "measurement_type": "reps",
        },
    ]

    service = Week1DosageService()
    dosages = service.generate(user, exercises)

    assert len(dosages) == 3

    squat = dosages[0]
    plank = dosages[1]
    wall_push_up = dosages[2]

    assert squat.exercise_id == "bodyweight_squat"
    assert squat.sets == 3
    assert squat.reps == 12
    assert squat.duration_seconds is None

    assert plank.exercise_id == "plank"
    assert plank.sets == 3
    assert plank.reps is None
    assert plank.duration_seconds == 30

    assert wall_push_up.exercise_id == "wall_push_up"
    assert wall_push_up.sets == 3
    assert wall_push_up.reps == 12
    assert wall_push_up.duration_seconds is None

    print("WEEK 1 DOSAGE SERVICE TESTS PASSED ✅")


if __name__ == "__main__":
    main()
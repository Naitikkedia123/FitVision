from data.exercise_catalog import EXERCISES
from planning.weekly_scheduler import generate_four_week_schedule


def _exercise_ids(day):
    return [exercise["id"] for exercise in day]


def main():
    low_activity = generate_four_week_schedule(
        eligible_exercises=EXERCISES,
        total_exercises=5,
        activity_level=1,
    )

    moderate_activity = generate_four_week_schedule(
        eligible_exercises=EXERCISES,
        total_exercises=5,
        activity_level=3,
    )

    high_activity = generate_four_week_schedule(
        eligible_exercises=EXERCISES,
        total_exercises=5,
        activity_level=5,
    )

    for schedule in (
        low_activity,
        moderate_activity,
        high_activity,
    ):
        assert set(schedule.keys()) == {1, 2, 3, 4}

        for week_number in range(1, 5):
            assert set(schedule[week_number].keys()) == {
                1, 2, 3, 4, 5, 6, 7
            }

            for day_number in range(1, 8):
                assert len(
                    schedule[week_number][day_number]
                ) == 5

    # Activity 1: same exercise set for all 7 days of Week 1.
    low_days = low_activity[1]

    assert (
        _exercise_ids(low_days[1])
        == _exercise_ids(low_days[7])
    )

    # Activity 3: first 4-day window remains the same.
    moderate_days = moderate_activity[1]

    assert (
        _exercise_ids(moderate_days[1])
        == _exercise_ids(moderate_days[4])
    )

    # A new rotation occurs on Day 5.
    assert (
        _exercise_ids(moderate_days[5])
        != _exercise_ids(moderate_days[4])
    )

    # Activity 5: daily rotation.
    high_days = high_activity[1]

    assert (
        _exercise_ids(high_days[1])
        != _exercise_ids(high_days[2])
    )

    print("ACTIVITY-BASED ROTATION TESTS PASSED ✅")


if __name__ == "__main__":
    main()
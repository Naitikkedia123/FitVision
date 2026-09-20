from data.exercise_catalog import EXERCISES
from rules.functional_eligibility import (
    FunctionalRestrictions,
    evaluate_exercise,
    filter_by_functional_restrictions,
)


def main() -> None:
    shoulder_press = next(
        exercise
        for exercise in EXERCISES
        if exercise["id"] == "shoulder_press"
    )

    plank = next(
        exercise
        for exercise in EXERCISES
        if exercise["id"] == "plank"
    )

    squat = next(
        exercise
        for exercise in EXERCISES
        if exercise["id"] == "bodyweight_squat"
    )

    # Explicit overhead restriction.
    shoulder_restriction = FunctionalRestrictions(
        avoid_overhead_shoulder=True
    )

    decision = evaluate_exercise(
        shoulder_press,
        shoulder_restriction,
    )

    assert not decision.eligible
    assert decision.reasons

    # Wrist weight-bearing restriction.
    wrist_restriction = FunctionalRestrictions(
        avoid_wrist_weight_bearing=True
    )

    decision = evaluate_exercise(
        plank,
        wrist_restriction,
    )

    assert not decision.eligible

    # A squat should remain eligible when no knee restriction
    # has actually been specified.
    unrestricted = FunctionalRestrictions()

    decision = evaluate_exercise(
        squat,
        unrestricted,
    )

    assert decision.eligible

    # Low-impact requirement.
    low_impact = FunctionalRestrictions(
        max_impact_level=0
    )

    eligible = filter_by_functional_restrictions(
        EXERCISES,
        low_impact,
    )

    assert all(
        exercise["impact_level"] <= 0
        for exercise in eligible
    )

    print("FUNCTIONAL ELIGIBILITY TESTS PASSED ✅")
    print(
        f"Exercises remaining with max impact 0: "
        f"{len(eligible)}"
    )


if __name__ == "__main__":
    main()
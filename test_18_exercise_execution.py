from shared.exercise_mapping import EXERCISE_EXECUTION_MAP
from integration.workout_adapter import adapt_workout_exercise
from ai_gym.services.execution.workout_controller import (
    WorkoutCommand,
    configure_workout,
)
import streamlit as st


def make_workout_row(exercise_id, index):
    spec = EXERCISE_EXECUTION_MAP[exercise_id]

    row = {
        "id": f"test-workout-exercise-{index}",
        "workout_day_id": "test-workout-day-1",
        "exercise_id": exercise_id,
        "order_index": index,
        "sets": 2,
        "target_reps": None,
        "target_duration_seconds": None,
    }

    if spec.measurement_type == "reps":
        row["target_reps"] = 12
    elif spec.measurement_type == "time":
        row["target_duration_seconds"] = 30
    else:
        raise AssertionError(
            f"Unknown measurement type: {spec.measurement_type}"
        )

    return row


def main():
    print("=" * 60)
    print("18 EXERCISE WORKOUT EXECUTION-FLOW TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    for index, exercise_id in enumerate(
        EXERCISE_EXECUTION_MAP.keys(),
        start=1,
    ):
        print(f"\nTesting: {exercise_id}")

        try:
            spec = EXERCISE_EXECUTION_MAP[exercise_id]

            if not spec.supported:
                raise AssertionError(
                    "Exercise is not marked as supported."
                )

            # -------------------------------------------------
            # Predictor-style persisted workout row
            # -------------------------------------------------
            row = make_workout_row(exercise_id, index)

            # -------------------------------------------------
            # Adapter
            # -------------------------------------------------
            config = adapt_workout_exercise(row)

            if config.exercise_id != exercise_id:
                raise AssertionError("Exercise ID mismatch.")

            if config.trainer_exercise_type != spec.trainer_exercise_type:
                raise AssertionError("Trainer exercise type mismatch.")

            if config.measurement_type != spec.measurement_type:
                raise AssertionError("Measurement type mismatch.")

            if config.sets != 2:
                raise AssertionError("Set count mismatch.")

            if spec.measurement_type == "reps":
                if config.target_reps != 12:
                    raise AssertionError("Rep target mismatch.")
                if config.target_duration_seconds is not None:
                    raise AssertionError(
                        "Time target must be None for rep exercise."
                    )
            else:
                if config.target_duration_seconds != 30:
                    raise AssertionError("Duration target mismatch.")
                if config.target_reps is not None:
                    raise AssertionError(
                        "Rep target must be None for time exercise."
                    )

            # -------------------------------------------------
            # WorkoutCommand
            # -------------------------------------------------
            if spec.measurement_type == "reps":
                command = WorkoutCommand(
                    exercise_id=exercise_id,
                    sets=2,
                    target_reps=12,
                    target_duration_seconds=None,
                    workout_exercise_id=row["id"],
                    workout_day_id=row["workout_day_id"],
                )
            else:
                command = WorkoutCommand(
                    exercise_id=exercise_id,
                    sets=2,
                    target_reps=None,
                    target_duration_seconds=30,
                    workout_exercise_id=row["id"],
                    workout_day_id=row["workout_day_id"],
                )

            command.validate()

            # -------------------------------------------------
            # Controller configuration
            # -------------------------------------------------
            configure_workout(command)

            if st.session_state["exercise_id"] != exercise_id:
                raise AssertionError(
                    "Controller exercise_id mismatch."
                )

            if (
                st.session_state["exercise_type"]
                != spec.trainer_exercise_type
            ):
                raise AssertionError(
                    "Controller trainer exercise type mismatch."
                )

            if st.session_state["target_sets"] != 2:
                raise AssertionError(
                    "Controller target_sets mismatch."
                )

            if spec.measurement_type == "reps":
                if st.session_state["reps_per_set"] != 12:
                    raise AssertionError(
                        "Controller reps_per_set mismatch."
                    )
                if st.session_state["target_duration_seconds"] is not None:
                    raise AssertionError(
                        "Controller duration should be None."
                    )
            else:
                if st.session_state["reps_per_set"] != 0:
                    raise AssertionError(
                        "Time exercise reps_per_set should be 0."
                    )
                if st.session_state["target_duration_seconds"] != 30:
                    raise AssertionError(
                        "Controller duration mismatch."
                    )

            # Fresh-state checks
            if st.session_state["reps"] != 0:
                raise AssertionError("Initial reps must be 0.")

            if st.session_state["current_set_reps"] != 0:
                raise AssertionError(
                    "Initial current_set_reps must be 0."
                )

            if st.session_state["sets_completed"] != 0:
                raise AssertionError(
                    "Initial sets_completed must be 0."
                )

            if st.session_state["workout_complete"] is not False:
                raise AssertionError(
                    "workout_complete must reset to False."
                )

            print(
                f"[PASS] {spec.trainer_exercise_type} "
                f"({spec.measurement_type})"
            )
            passed += 1

        except Exception as exc:
            print(f"[FAIL] {exercise_id}: {exc}")
            failed += 1

    print("\n" + "=" * 60)
    print(
        f"RESULT: {passed}/18 passed, "
        f"{failed}/18 failed"
    )
    print("=" * 60)

    if failed == 0:
        print("ALL 18 EXECUTION-FLOW TESTS PASSED")
    else:
        print("SOME EXECUTION-FLOW TESTS FAILED")


if __name__ == "__main__":
    main()

import sys
import types
from types import SimpleNamespace


# ============================================================
# MOCK DATABASE MODULE
# ============================================================

database_module = types.ModuleType("database")
database_client_module = types.ModuleType("database.client")


def fake_get_supabase_client():
    return None


database_client_module.get_supabase_client = (
    fake_get_supabase_client
)

database_module.client = database_client_module

sys.modules["database"] = database_module
sys.modules["database.client"] = database_client_module


# ============================================================
# IMPORT METRICS AFTER DATABASE MOCK
# ============================================================

import ai_gym.services.tracking.metrics as metrics_module


# ============================================================
# FAKE SESSION STATE
# ============================================================

class FakeSessionState(dict):
    """Minimal Streamlit session_state replacement."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class FakeStreamlit:

    def __init__(self):
        self.session_state = FakeSessionState()

    def rerun(self):
        raise RuntimeError(
            "Unexpected rerun during persistence test"
        )


# ============================================================
# FAKE VIDEO PROCESSOR
# ============================================================

class FakeProcessor:

    def __init__(self, duration_seconds):
        self.duration_seconds = duration_seconds

    def set_exercise(self, exercise):
        pass

    def get_latest_metrics(self):
        return {
            "duration_seconds": self.duration_seconds,
            "stage": "marching",
        }


# ============================================================
# FAKE REPOSITORY
# ============================================================

class FakeWorkoutPlanRepository:

    calls = []

    def __init__(self):
        pass

    def update_exercise_progress(
        self,
        workout_exercise_id,
        completed_sets,
    ):
        self.__class__.calls.append(
            {
                "workout_exercise_id": (
                    workout_exercise_id
                ),
                "completed_sets": (
                    completed_sets
                ),
            }
        )


# ============================================================
# RUN ONE PERSISTENCE TEST
# ============================================================

def run_test(
    duration_seconds,
    expected_sets,
):
    fake_st = FakeStreamlit()

    original_st = metrics_module.st
    original_repository = (
        metrics_module.WorkoutPlanRepository
    )
    original_fields = (
        metrics_module.METRICS_FIELDS
    )

    metrics_module.st = fake_st

    metrics_module.WorkoutPlanRepository = (
        FakeWorkoutPlanRepository
    )

    FakeWorkoutPlanRepository.calls = []

    try:

        # ----------------------------------------------------
        # Workout configuration
        # ----------------------------------------------------

        fake_st.session_state[
            "exercise_type"
        ] = "march_in_place"

        fake_st.session_state[
            "target_sets"
        ] = 2

        fake_st.session_state[
            "target_duration_seconds"
        ] = 30

        fake_st.session_state[
            "reps_per_set"
        ] = 0

        fake_st.session_state[
            "workout_started"
        ] = False

        # ----------------------------------------------------
        # Simulate an active Supabase workout exercise.
        # ----------------------------------------------------

        fake_st.session_state[
            "active_workout_exercise"
        ] = {
            "id": "test-workout-exercise-123",
            "completed_sets": 0,
            "required_sets": 2,
        }

        fake_st.session_state[
            "workout_exercise_id"
        ] = "test-workout-exercise-123"

        # ----------------------------------------------------
        # Detector/session starts with 0 persisted sets.
        # ----------------------------------------------------

        fake_st.session_state[
            "_persisted_completed_sets"
        ] = 0

        # ----------------------------------------------------
        # Prevent any previous save state from interfering.
        # ----------------------------------------------------

        fake_st.session_state[
            "last_saved_sets_completed"
        ] = 0

        # ----------------------------------------------------
        # Required metric fields.
        # ----------------------------------------------------

        metrics_module.METRICS_FIELDS = {
            **original_fields,
            "march_in_place": {
                "duration_seconds": 0.0,
                "stage": "not_marching",
            },
        }

        # ----------------------------------------------------
        # Fake detector output.
        # ----------------------------------------------------

        processor = FakeProcessor(
            duration_seconds
        )

        context = SimpleNamespace(
            state=SimpleNamespace(
                playing=True
            ),
            video_processor=processor,
        )

        # ----------------------------------------------------
        # Run actual metrics code.
        # ----------------------------------------------------

        metrics_module.sync_metrics_update(
            context
        )

        # ----------------------------------------------------
        # Verify calculated sets.
        # ----------------------------------------------------

        actual_sets = (
            fake_st.session_state.get(
                "sets_completed"
            )
        )

        if actual_sets != expected_sets:

            print(
                f"[FAIL] {duration_seconds}s: "
                f"expected {expected_sets} sets, "
                f"got {actual_sets}"
            )

            return False

        # ----------------------------------------------------
        # Verify repository call.
        # ----------------------------------------------------

        calls = (
            FakeWorkoutPlanRepository.calls
        )

        if expected_sets == 0:

            if calls:

                print(
                    f"[FAIL] {duration_seconds}s: "
                    f"repository was called even though "
                    f"no set was completed"
                )

                return False

            print(
                f"[PASS] {duration_seconds:>5}s -> "
                f"0 sets, no database update"
            )

            return True

        # ----------------------------------------------------
        # A completed set should have been persisted.
        # ----------------------------------------------------

        if len(calls) != 1:

            print(
                f"[FAIL] {duration_seconds}s: "
                f"expected 1 repository call, "
                f"got {len(calls)}"
            )

            return False

        call = calls[0]

        if (
            call["workout_exercise_id"]
            != "test-workout-exercise-123"
        ):

            print(
                f"[FAIL] {duration_seconds}s: "
                f"incorrect workout_exercise_id: "
                f"{call['workout_exercise_id']}"
            )

            return False

        if (
            call["completed_sets"]
            != expected_sets
        ):

            print(
                f"[FAIL] {duration_seconds}s: "
                f"expected database completed_sets="
                f"{expected_sets}, "
                f"got {call['completed_sets']}"
            )

            return False

        print(
            f"[PASS] {duration_seconds:>5}s -> "
            f"{expected_sets} sets persisted"
        )

        return True

    finally:

        metrics_module.st = original_st

        metrics_module.WorkoutPlanRepository = (
            original_repository
        )

        metrics_module.METRICS_FIELDS = (
            original_fields
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "TIME-BASED PERSISTENCE TEST"
    )
    print("=" * 60)

    tests = [
        (29, 0),
        (30, 1),
        (60, 2),
    ]

    passed = 0

    for duration, expected_sets in tests:

        if run_test(
            duration,
            expected_sets,
        ):
            passed += 1

    print("=" * 60)

    print(
        f"RESULT: "
        f"{passed}/{len(tests)} tests passed"
    )

    print("=" * 60)

    if passed == len(tests):

        print(
            "ALL TIME-BASED PERSISTENCE TESTS PASSED"
        )

    else:

        print(
            "TIME-BASED PERSISTENCE TEST FAILED"
        )


if __name__ == "__main__":
    main()
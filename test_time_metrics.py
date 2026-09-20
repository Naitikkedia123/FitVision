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
# NOW IMPORT METRICS
# ============================================================

import ai_gym.services.tracking.metrics as metrics_module


# ============================================================
# FAKE STREAMLIT
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
            "Unexpected rerun during test"
        )


# ============================================================
# FAKE VIDEO PROCESSOR
# ============================================================

class FakeProcessor:

    def __init__(self):
        self.latest_metrics = {}

    def set_exercise(self, exercise):
        pass

    def get_latest_metrics(self):
        return self.latest_metrics


# ============================================================
# TEST ONE DURATION
# ============================================================

def run_test(
    duration_seconds,
    expected_sets,
    expected_completed,
):
    fake_st = FakeStreamlit()

    original_st = metrics_module.st
    original_fields = metrics_module.METRICS_FIELDS

    metrics_module.st = fake_st

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

        # No previously completed sets.
        fake_st.session_state[
            "_persisted_completed_sets"
        ] = 0

        # Prevent completion flow from trying
        # to return to the dashboard.
        fake_st.session_state[
            "workout_started"
        ] = False

        # ----------------------------------------------------
        # Fake detector metrics
        # ----------------------------------------------------

        processor = FakeProcessor()

        processor.latest_metrics = {
            "duration_seconds": duration_seconds,
            "stage": "marching",
        }

        context = SimpleNamespace(
            state=SimpleNamespace(
                playing=True
            ),
            video_processor=processor,
        )

        # ----------------------------------------------------
        # Provide the required metric fields
        # ----------------------------------------------------

        metrics_module.METRICS_FIELDS = {
            **original_fields,
            "march_in_place": {
                "duration_seconds": 0.0,
                "stage": "not_marching",
            },
        }

        # ----------------------------------------------------
        # Run the ACTUAL metrics function
        # ----------------------------------------------------

        metrics_module.sync_metrics_update(
            context
        )

        actual_sets = fake_st.session_state.get(
            "sets_completed"
        )

        actual_completed = fake_st.session_state.get(
            "workout_completed"
        )

        # ----------------------------------------------------
        # Verify sets
        # ----------------------------------------------------

        if actual_sets != expected_sets:

            print(
                f"[FAIL] {duration_seconds}s: "
                f"expected {expected_sets} sets, "
                f"got {actual_sets}"
            )

            return False

        # ----------------------------------------------------
        # Verify completion
        # ----------------------------------------------------

        if actual_completed != expected_completed:

            print(
                f"[FAIL] {duration_seconds}s: "
                f"expected completed="
                f"{expected_completed}, "
                f"got {actual_completed}"
            )

            return False

        print(
            f"[PASS] {duration_seconds:>5}s -> "
            f"{actual_sets}/2 sets, "
            f"completed={actual_completed}"
        )

        return True

    finally:

        metrics_module.st = original_st

        metrics_module.METRICS_FIELDS = (
            original_fields
        )


# ============================================================
# MAIN TEST
# ============================================================

def main():

    print("=" * 60)
    print(
        "TIME-BASED METRICS PROGRESS TEST"
    )
    print("=" * 60)

    tests = [
        (29, 0, False),
        (30, 1, False),
        (45, 1, False),
        (59, 1, False),
        (60, 2, True),
    ]

    passed = 0

    for (
        duration,
        expected_sets,
        expected_completed,
    ) in tests:

        if run_test(
            duration,
            expected_sets,
            expected_completed,
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
            "ALL TIME-BASED METRICS TESTS PASSED"
        )

    else:

        print(
            "TIME-BASED METRICS TEST FAILED"
        )


if __name__ == "__main__":
    main()
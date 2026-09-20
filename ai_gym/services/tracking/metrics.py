import streamlit as st
import time

from ai_gym.services.config.workout_config import METRICS_FIELDS
from fitness_predictor.database.repositories.workout_plan_repository import (
    WorkoutPlanRepository,
)

def update_dashboard_plan_cache(
    workout_exercise_id,
    completed_sets,
) -> None:
    """
    Keep the in-memory dashboard plan synchronized with
    authoritative Supabase workout progress.
    """

    plan = st.session_state.get(
        "dashboard_plan_cache"
    )

    if not isinstance(plan, dict):
        return

    exercise_id = str(
        workout_exercise_id
    )

    completed_sets = int(
        completed_sets
    )

    for day in plan.get(
        "days",
        [],
    ):

        exercises = day.get(
            "exercises",
            [],
        )

        for exercise in exercises:

            if str(
                exercise.get("id")
            ) != exercise_id:
                continue

            required_sets = exercise.get(
                "sets"
            )

            if required_sets is not None:
                required_sets = int(
                    required_sets
                )

                completed_sets = min(
                    completed_sets,
                    required_sets,
                )

            exercise[
                "completed_sets"
            ] = completed_sets

            if (
                required_sets is not None
                and completed_sets >= required_sets
            ):
                exercise[
                    "status"
                ] = "completed"
            else:
                exercise[
                    "status"
                ] = "in_progress"

            # Recalculate whether this entire workout day
            # is now complete.
            day_completed = (
                bool(exercises)
                and all(
                    str(
                        item.get("status") or ""
                    ).strip().lower()
                    == "completed"
                    for item in exercises
                )
            )

            day[
                "is_completed"
            ] = day_completed

            if day_completed:
                day[
                    "workout_state"
                ] = "completed"

            return


def sync_metrics_update(context):
    if (
        not context
        or not hasattr(context, "state")
        or not context.state.playing
    ):
        return

    processor = getattr(context, "video_processor", None)

    if not processor:
        return

    exercise = st.session_state.get("exercise_type")

    if not exercise:
        return

    processor.set_exercise(exercise)
    latest_metrics = processor.get_latest_metrics()

    if not latest_metrics:
        return

    # =========================================================
    # LOAD PERSISTED PROGRESS
    # =========================================================

    workout_exercise = st.session_state.get(
        "active_workout_exercise"
    )

    workout_exercise_id = st.session_state.get(
        "workout_exercise_id"
    )

    progress_loaded_for = st.session_state.get(
        "_progress_loaded_for_exercise"
    )

    if (
        workout_exercise
        and workout_exercise_id
        and progress_loaded_for != str(workout_exercise_id)
    ):
        persisted_completed_sets = (
            workout_exercise.get("completed_sets") or 0
        )

        st.session_state[
            "_persisted_completed_sets"
        ] = int(persisted_completed_sets)

        st.session_state[
            "_progress_loaded_for_exercise"
        ] = str(workout_exercise_id)

    persisted_completed_sets = st.session_state.get(
        "_persisted_completed_sets",
        0,
    )

    # =========================================================
    # READ DETECTOR METRICS
    # =========================================================

    session_reps = latest_metrics.get(
        "reps",
        0,
    )

    if session_reps is None:
        session_reps = 0

    session_reps = int(session_reps)

    fields = METRICS_FIELDS.get(exercise)

    if not fields:
        return

    for key, default in fields.items():
        st.session_state[key] = latest_metrics.get(
            key,
            default,
        )

    # =========================================================
    # WORKOUT TARGET
    # =========================================================

    reps_per_set = st.session_state.get(
        "reps_per_set",
        0,
    )

    target_sets = st.session_state.get(
        "target_sets",
        0,
    )

    target_duration_seconds = st.session_state.get(
        "target_duration_seconds"
    )

    # =========================================================
    # DETERMINE MEASUREMENT TYPE
    # =========================================================

    is_rep_based = (
        reps_per_set > 0
        and target_sets > 0
    )

    is_time_based = (
        target_duration_seconds is not None
        and int(target_duration_seconds) > 0
        and target_sets > 0
    )

    # =========================================================
    # REP-BASED EXERCISE
    # =========================================================

    if is_rep_based:

        persisted_reps = (
            persisted_completed_sets
            * reps_per_set
        )

        total_reps = (
            persisted_reps
            + session_reps
        )

        session_sets_completed = (
            session_reps // reps_per_set
        )

        sets_completed = (
            persisted_completed_sets
            + session_sets_completed
        )

        current_set_reps = (
            session_reps % reps_per_set
        )

        exercise_completed = (
            sets_completed >= target_sets
        )

        current_set_duration = 0
        total_duration = 0

    # =========================================================
    # TIME-BASED EXERCISE
    # =========================================================

    elif is_time_based:

        target_duration_seconds = int(
            target_duration_seconds
        )

        session_duration = latest_metrics.get(
            "duration_seconds",
            0,
        )

        if session_duration is None:
            session_duration = 0

        try:
            session_duration = float(
                session_duration
            )
        except (TypeError, ValueError):
            session_duration = 0.0

        session_duration = max(
            0.0,
            session_duration,
        )

        # -----------------------------------------------------
        # Convert detector duration into completed sets.
        #
        # Example:
        #
        # target = 30 sec
        #
        # duration = 29 sec
        #   -> 0 sets
        #
        # duration = 30 sec
        #   -> 1 set
        #
        # duration = 45 sec
        #   -> 1 set + 15 sec
        #
        # duration = 60 sec
        #   -> 2 sets
        # -----------------------------------------------------

        session_sets_completed = int(
            session_duration
            // target_duration_seconds
        )

        sets_completed = (
            persisted_completed_sets
            + session_sets_completed
        )

        current_set_duration = (
            session_duration
            % target_duration_seconds
        )

        total_duration = (
            persisted_completed_sets
            * target_duration_seconds
            + session_duration
        )

        # Time-based exercises do not use reps.
        total_reps = 0
        current_set_reps = 0

        exercise_completed = (
            sets_completed >= target_sets
        )

    # =========================================================
    # INVALID / MISSING TARGET
    # =========================================================

    else:

        total_reps = session_reps

        sets_completed = (
            persisted_completed_sets
        )

        current_set_reps = 0

        current_set_duration = 0
        total_duration = 0

        exercise_completed = False

    # =========================================================
    # UPDATE SESSION STATE
    # =========================================================

    st.session_state.reps = (
        total_reps
    )

    st.session_state.sets_completed = (
        sets_completed
    )

    st.session_state.current_set_reps = (
        current_set_reps
    )

    st.session_state.current_set_duration = (
        current_set_duration
    )

    st.session_state.total_duration = (
        total_duration
    )

    st.session_state.workout_completed = (
        exercise_completed
    )

    # =========================================================
    # PERSIST NEWLY COMPLETED SETS
    # =========================================================

    last_saved_sets = st.session_state.get(
        "last_saved_sets_completed",
        persisted_completed_sets,
    )

    # Never allow local progress to move behind
    # persisted Supabase progress.
    if last_saved_sets < persisted_completed_sets:
        last_saved_sets = (
            persisted_completed_sets
        )

    if (
        target_sets > 0
        and sets_completed > last_saved_sets
    ):

        newly_completed = (
            sets_completed
            - last_saved_sets
        )

        now_ts = time.time()

        started_at = st.session_state.get(
            "set_cycle_started_at",
            now_ts,
        )

        time_taken = (
            now_ts
            - started_at
        )

        user_id = st.session_state.get(
            "user_id",
            0,
        )

        # -----------------------------------------------------
        # Authoritative workout-plan persistence
        # -----------------------------------------------------

        if workout_exercise_id:

            repository = WorkoutPlanRepository()

            repository.update_exercise_progress(
                workout_exercise_id=str(
                    workout_exercise_id
                ),
                completed_sets=int(
                    sets_completed
                ),
            )

            # Supabase is authoritative. Only update the dashboard
            # cache after the database update succeeds.
            update_dashboard_plan_cache(
                workout_exercise_id=workout_exercise_id,
                completed_sets=sets_completed,
            )

        # -----------------------------------------------------
        # Existing voice coaching
        # -----------------------------------------------------

        if st.session_state.get(
            "voice_pipeline"
        ):

            result = (
                st.session_state.voice_pipeline.process_event(
                    event="set_completed",
                    exercise=exercise,
                    metrics=latest_metrics,
                )
            )

            if result:

                (
                    st.session_state.audio_to_play,
                    st.session_state.coach_feedback,
                ) = result

        st.session_state.set_cycle_started_at = (
            now_ts
        )

        st.session_state.last_saved_sets_completed = (
            sets_completed
        )

    # =========================================================
    # EXERCISE COMPLETION
    #
    # Automatic next-exercise progression is intentionally
    # disabled for now.
    #
    # Once the configured exercise reaches its target,
    # the current workout session ends and the user returns
    # to the dashboard.
    # =========================================================

    if (
        exercise_completed
        and st.session_state.get("workout_started")
    ):

        workout_day_id = st.session_state.get(
            "workout_day_id"
        )

        current_exercise = st.session_state.get(
            "active_workout_exercise"
        )

        if (
            workout_exercise_id
            and workout_day_id
            and current_exercise
        ):

            st.session_state[
                "workout_started"
            ] = False

            st.session_state[
                "workout_complete"
            ] = False

            st.session_state[
                "workout_completed"
            ] = False

            st.session_state.pop(
                "active_workout_command",
                None,
            )

            st.session_state.pop(
                "active_workout_exercise_id",
                None,
            )

            st.session_state.pop(
                "active_workout_exercise",
                None,
            )

            st.session_state.pop(
                "_active_workout_command",
                None,
            )

            st.session_state[
                "returning_from_workout"
            ] = True

            st.session_state[
                "screen"
            ] = "dashboard"

            st.rerun()

    # =========================================================
    # NO-POSE FEEDBACK
    # =========================================================

    pose_detected = latest_metrics.get(
        "pose_detected",
        True,
    )

    if (
        not pose_detected
        and st.session_state.get("voice_pipeline")
        and not exercise_completed
    ):

        result = (
            st.session_state.voice_pipeline.process_event(
                event="no_pose_detected",
                exercise=exercise,
                metrics={
                    "issue": (
                        "No pose detected! "
                        "Please step into the camera frame."
                    )
                },
            )
        )

        if result:

            (
                st.session_state.audio_to_play,
                st.session_state.coach_feedback,
            ) = result

    # =========================================================
    # ONGOING FORM FEEDBACK
    # =========================================================

    if (
        st.session_state.get("voice_pipeline")
        and not exercise_completed
    ):

        result = (
            st.session_state.voice_pipeline.process_event(
                event="ongoing_form_check",
                exercise=exercise,
                metrics=latest_metrics,
            )
        )

        if result:

            (
                st.session_state.audio_to_play,
                st.session_state.coach_feedback,
            ) = result
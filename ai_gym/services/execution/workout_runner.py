from __future__ import annotations

import time
from dataclasses import dataclass

import streamlit as st

from ai_gym.services.execution.workout_controller import (
    WorkoutCommand,
    configure_workout,
)

from ai_gym.services.vision.landmark_processor import (
    LandmarkProcessor,
)

from ai_gym.services.vision.local_camera_component import (
    render_local_camera,
)


# =========================================================
# Trainer context
# =========================================================

@dataclass
class _TrainerState:
    playing: bool = False


@dataclass
class _TrainerContext:
    state: _TrainerState
    video_processor: LandmarkProcessor


# =========================================================
# Landmark processor
# =========================================================

def _get_landmark_processor() -> LandmarkProcessor:
    processor = st.session_state.get(
        "_local_landmark_processor"
    )

    if processor is None:
        processor = LandmarkProcessor()

        st.session_state[
            "_local_landmark_processor"
        ] = processor

    return processor


# =========================================================
# Workout runner
# =========================================================

def render_workout_runner(
    command: WorkoutCommand,
):
    command.validate()

    configured_command = st.session_state.get(
        "_active_workout_command"
    )

    processor = _get_landmark_processor()

    # -----------------------------------------------------
    # Configure a genuinely new workout/exercise
    # -----------------------------------------------------

    if configured_command != command:

        configure_workout(
            command
        )

        st.session_state[
            "_active_workout_command"
        ] = command

        st.session_state[
            "workout_started"
        ] = True

        st.session_state[
            "set_cycle_started_at"
        ] = time.time()

        st.session_state[
            "last_saved_sets_completed"
        ] = 0

        st.session_state.pop(
            "_last_local_camera_packet",
            None,
        )

        # -------------------------------------------------
        # IMPORTANT:
        # Start the detector from a clean state.
        #
        # This happens only when the command changes
        # or a new workout is started.
        # It does NOT happen every 0.25 seconds.
        # -------------------------------------------------

        processor.set_exercise(
            command.exercise_id
        )

        processor.reset_current_exercise()

    else:

        # Same exercise continues normally.
        # Do NOT reset the detector here.

        processor.set_exercise(
            command.exercise_id
        )

    # -----------------------------------------------------
    # Browser-local camera
    # -----------------------------------------------------

    packet = render_local_camera(
        exercise_type=(
            processor.get_exercise()
        ),
        key="fitvision-local-camera",
        inference_interval_ms=250,
    )

    camera_playing = False

    # -----------------------------------------------------
    # Process latest landmark packet
    # -----------------------------------------------------

    if isinstance(
        packet,
        dict,
    ):

        camera_playing = bool(
            packet.get(
                "camera_active",
                False,
            )
        )

        landmark_frames = packet.get(
            "landmark_frames",
            [],
        )

        if landmark_frames:

            processor.process_landmark_batch(
                landmark_frames
            )

        st.session_state[
            "_last_local_camera_packet"
        ] = packet

    # -----------------------------------------------------
    # Preserve previous state
    # -----------------------------------------------------

    else:

        previous_packet = (
            st.session_state.get(
                "_last_local_camera_packet"
            )
        )

        if isinstance(
            previous_packet,
            dict,
        ):

            camera_playing = bool(
                previous_packet.get(
                    "camera_active",
                    False,
                )
            )

    # -----------------------------------------------------
    # Return trainer context
    # -----------------------------------------------------

    return _TrainerContext(
        state=_TrainerState(
            playing=camera_playing
        ),
        video_processor=processor,
    )
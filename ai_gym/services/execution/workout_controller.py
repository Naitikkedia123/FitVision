from dataclasses import dataclass

import streamlit as st

from shared.exercise_mapping import get_trainer_exercise_type


@dataclass(frozen=True)
class WorkoutCommand:
    """Configuration required to start one workout exercise."""

    exercise_id: str
    sets: int
    target_reps: int | None = None
    target_duration_seconds: int | None = None
    workout_exercise_id: str | None = None
    workout_day_id: str | None = None

    def validate(self) -> None:
        if not isinstance(self.exercise_id, str) or not self.exercise_id.strip():
            raise ValueError("exercise_id must be a non-empty string.")

        if not isinstance(self.sets, int) or self.sets <= 0:
            raise ValueError("sets must be a positive integer.")

        if self.target_reps is None and self.target_duration_seconds is None:
            raise ValueError(
                "Exactly one of target_reps or "
                "target_duration_seconds is required."
            )

        if (
            self.target_reps is not None
            and self.target_duration_seconds is not None
        ):
            raise ValueError(
                "target_reps and target_duration_seconds "
                "cannot both be set."
            )

        if self.target_reps is not None:
            if not isinstance(self.target_reps, int) or self.target_reps <= 0:
                raise ValueError(
                    "target_reps must be a positive integer."
                )

        if self.target_duration_seconds is not None:
            if (
                not isinstance(self.target_duration_seconds, int)
                or self.target_duration_seconds <= 0
            ):
                raise ValueError(
                    "target_duration_seconds must be a positive integer."
                )


def configure_workout(command: WorkoutCommand) -> None:
    """
    Configure an AI GYM workout without performing execution logic.

    Rep counting, set tracking, persistence, and coaching remain
    in the existing execution/tracking layer.
    """
    command.validate()

    trainer_exercise_type = get_trainer_exercise_type(
        command.exercise_id
    )

    st.session_state["exercise_id"] = command.exercise_id
    st.session_state["exercise_type"] = trainer_exercise_type

    st.session_state["target_sets"] = command.sets
    st.session_state["reps_per_set"] = (
        command.target_reps
        if command.target_reps is not None
        else 0
    )

    st.session_state["target_duration_seconds"] = (
        command.target_duration_seconds
    )

    st.session_state["workout_exercise_id"] = (
        command.workout_exercise_id
    )

    st.session_state["workout_day_id"] = (
        command.workout_day_id
    )

    # Fresh execution state.
    st.session_state["reps"] = 0
    st.session_state["current_set_reps"] = 0
    st.session_state["sets_completed"] = 0
    st.session_state["workout_complete"] = False
    st.session_state["workout_completed"] = False
    st.session_state["last_saved_sets_completed"] = 0
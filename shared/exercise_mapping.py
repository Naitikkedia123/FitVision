from dataclasses import dataclass


@dataclass(frozen=True)
class ExerciseExecutionSpec:
    """
    Defines how a fitness_predictor exercise is executed
    by the AI GYM trainer.

    This is the shared execution contract between the
    fitness predictor and the AI GYM execution layer.

    The predictor owns exercise/safety/planning metadata.

    This registry owns execution-specific metadata only.
    """

    # ---------------------------------------------------------
    # Canonical identity
    # ---------------------------------------------------------

    exercise_id: str

    # ---------------------------------------------------------
    # AI GYM execution identity
    # ---------------------------------------------------------

    trainer_exercise_type: str | None

    # ---------------------------------------------------------
    # Execution capability
    # ---------------------------------------------------------

    supported: bool

    # ---------------------------------------------------------
    # Execution metadata
    # ---------------------------------------------------------

    measurement_type: str
    camera_view: str
    required_landmarks: tuple[str, ...]


# =========================================================
# Central exercise execution registry
# =========================================================

EXERCISE_EXECUTION_MAP: dict[str, ExerciseExecutionSpec] = {

    # =====================================================
    # Cardio
    # =====================================================

    "march_in_place": ExerciseExecutionSpec(
        exercise_id="march_in_place",
        trainer_exercise_type="March in Place",
        supported=True,
        measurement_type="time",
        camera_view="front",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "standing_knee_raise": ExerciseExecutionSpec(
        exercise_id="standing_knee_raise",
        trainer_exercise_type="Standing Knee Raises",
        supported=True,
        measurement_type="reps",
        camera_view="front",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "low_impact_jumping_jack": ExerciseExecutionSpec(
        exercise_id="low_impact_jumping_jack",
        trainer_exercise_type="Low-Impact Jumping Jacks",
        supported=True,
        measurement_type="reps",
        camera_view="front",
        required_landmarks=(
            "shoulders",
            "hips",
            "knees",
            "ankles",
        ),
    ),

    # =====================================================
    # Lower body
    # =====================================================

    "bodyweight_squat": ExerciseExecutionSpec(
        exercise_id="bodyweight_squat",
        trainer_exercise_type="Squats",
        supported=True,
        measurement_type="reps",
        camera_view="side",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "reverse_lunge": ExerciseExecutionSpec(
        exercise_id="reverse_lunge",
        trainer_exercise_type="Lunges",
        supported=True,
        measurement_type="reps",
        camera_view="front",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "wall_sit": ExerciseExecutionSpec(
        exercise_id="wall_sit",
        trainer_exercise_type="Wall Sits",
        supported=True,
        measurement_type="time",
        camera_view="side",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "standing_side_leg_raise": ExerciseExecutionSpec(
        exercise_id="standing_side_leg_raise",
        trainer_exercise_type="Standing Side Leg Raises",
        supported=True,
        measurement_type="reps",
        camera_view="front",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "hamstring_curl": ExerciseExecutionSpec(
        exercise_id="hamstring_curl",
        trainer_exercise_type="Standing Hamstring Curls",
        supported=True,
        measurement_type="reps",
        camera_view="side",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "hip_extension": ExerciseExecutionSpec(
        exercise_id="hip_extension",
        trainer_exercise_type="Standing Hip Extensions",
        supported=True,
        measurement_type="reps",
        camera_view="side",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "calf_raise": ExerciseExecutionSpec(
        exercise_id="calf_raise",
        trainer_exercise_type="Calf Raises",
        supported=True,
        measurement_type="reps",
        camera_view="front",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "glute_bridge": ExerciseExecutionSpec(
        exercise_id="glute_bridge",
        trainer_exercise_type="Glute Bridges",
        supported=True,
        measurement_type="reps",
        camera_view="side",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "sit_to_stand": ExerciseExecutionSpec(
        exercise_id="sit_to_stand",
        trainer_exercise_type="Sit-to-Stands",
        supported=True,
        measurement_type="reps",
        camera_view="side",
        required_landmarks=(
            "hips",
            "knees",
            "ankles",
        ),
    ),

    # =====================================================
    # Upper body
    # =====================================================

    "wall_push_up": ExerciseExecutionSpec(
        exercise_id="wall_push_up",
        trainer_exercise_type="Wall Push-Ups",
        supported=True,
        measurement_type="reps",
        camera_view="side",
        required_landmarks=(
            "shoulders",
            "elbows",
            "wrists",
        ),
    ),

    "knee_push_up": ExerciseExecutionSpec(
        exercise_id="knee_push_up",
        trainer_exercise_type="Knee Push-Ups",
        supported=True,
        measurement_type="reps",
        camera_view="side",
        required_landmarks=(
            "shoulders",
            "elbows",
            "wrists",
            "hips",
            "knees",
        ),
    ),

    "standard_push_up": ExerciseExecutionSpec(
        exercise_id="standard_push_up",
        trainer_exercise_type="Push-ups",
        supported=True,
        measurement_type="reps",
        camera_view="side",
        required_landmarks=(
            "shoulders",
            "elbows",
            "wrists",
            "hips",
            "knees",
            "ankles",
        ),
    ),

    "shoulder_press": ExerciseExecutionSpec(
        exercise_id="shoulder_press",
        trainer_exercise_type="Shoulder Press",
        supported=True,
        measurement_type="reps",
        camera_view="front",
        required_landmarks=(
            "shoulders",
            "elbows",
            "wrists",
            "hips",
            "knees",
        ),
    ),

    "biceps_curl": ExerciseExecutionSpec(
        exercise_id="biceps_curl",
        trainer_exercise_type="Biceps Curls (Dumbbell)",
        supported=True,
        measurement_type="reps",
        camera_view="front",
        required_landmarks=(
            "shoulders",
            "elbows",
            "wrists",
        ),
    ),

    # =====================================================
    # Core
    # =====================================================

    "plank": ExerciseExecutionSpec(
        exercise_id="plank",
        trainer_exercise_type="Planks",
        supported=True,
        measurement_type="time",
        camera_view="side",
        required_landmarks=(
            "shoulders",
            "hips",
            "knees",
            "ankles",
        ),
    ),
}


# =========================================================
# Registry access
# =========================================================

def get_execution_spec(
    exercise_id: str,
) -> ExerciseExecutionSpec:
    """
    Return the execution specification for an exercise.
    """

    if not isinstance(exercise_id, str):
        raise TypeError(
            "exercise_id must be a string."
        )

    exercise_id = exercise_id.strip()

    if not exercise_id:
        raise ValueError(
            "exercise_id cannot be empty."
        )

    try:
        return EXERCISE_EXECUTION_MAP[
            exercise_id
        ]

    except KeyError as exc:

        raise ValueError(
            f"Unknown exercise_id: {exercise_id}"
        ) from exc


def is_trainer_supported(
    exercise_id: str,
) -> bool:
    """
    Return whether AI GYM currently has an execution
    implementation for the given exercise.
    """

    return get_execution_spec(
        exercise_id
    ).supported


def get_trainer_exercise_type(
    exercise_id: str,
) -> str:
    """
    Return the AI GYM execution key for an exercise.

    Raises ValueError when the exercise does not currently
    have an execution implementation.
    """

    spec = get_execution_spec(
        exercise_id
    )

    if (
        not spec.supported
        or spec.trainer_exercise_type is None
    ):
        raise ValueError(
            f"Exercise '{exercise_id}' does not "
            "currently have an AI GYM execution "
            "implementation."
        )

    return spec.trainer_exercise_type


def get_exercise_id_for_trainer_type(
    trainer_exercise_type: str,
) -> str:
    """
    Return the canonical exercise ID for an AI GYM
    trainer exercise type.
    """

    if not isinstance(
        trainer_exercise_type,
        str,
    ):
        raise TypeError(
            "trainer_exercise_type must be a string."
        )

    trainer_exercise_type = (
        trainer_exercise_type.strip()
    )

    if not trainer_exercise_type:
        raise ValueError(
            "trainer_exercise_type cannot be empty."
        )

    for (
        exercise_id,
        spec,
    ) in EXERCISE_EXECUTION_MAP.items():

        if (
            spec.trainer_exercise_type
            == trainer_exercise_type
        ):
            return exercise_id

    raise ValueError(
        "Unknown trainer exercise type: "
        f"{trainer_exercise_type}"
    )
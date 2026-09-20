from dataclasses import dataclass
from typing import Literal


MeasurementType = Literal["reps", "time"]


@dataclass(frozen=True)
class TrainingTarget:
    measurement_type: MeasurementType
    target_name: str


TRAINING_TARGETS = {
    "reps": TrainingTarget(
        measurement_type="reps",
        target_name="target_reps",
    ),
    "time": TrainingTarget(
        measurement_type="time",
        target_name="target_duration_seconds",
    ),
}


USER_FEATURES = [
    "age",
    "height_cm",
    "weight_kg",
    "fitness_level",
    "activity_level",
]


EXERCISE_FEATURES = [
    "difficulty",
    "impact_level",
    "knee_flexion_level",
    "hip_load_level",
    "shoulder_overhead_required",
    "wrist_weight_bearing",
    "back_load_level",
    "ankle_load_level",
    "floor_required",
    "single_leg",
]
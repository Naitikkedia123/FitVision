from shared.exercise_mapping import EXERCISE_EXECUTION_MAP
from ai_gym.services.vision.landmark_processor import LandmarkProcessor

expected = {
    "march_in_place": "March in Place",
    "standing_knee_raise": "Standing Knee Raises",
    "low_impact_jumping_jack": "Low-Impact Jumping Jacks",
    "bodyweight_squat": "Squats",
    "reverse_lunge": "Lunges",
    "wall_sit": "Wall Sits",
    "standing_side_leg_raise": "Standing Side Leg Raises",
    "hamstring_curl": "Standing Hamstring Curls",
    "hip_extension": "Standing Hip Extensions",
    "calf_raise": "Calf Raises",
    "glute_bridge": "Glute Bridges",
    "sit_to_stand": "Sit-to-Stands",
    "wall_push_up": "Wall Push-Ups",
    "knee_push_up": "Knee Push-Ups",
    "standard_push_up": "Push-ups",
    "shoulder_press": "Shoulder Press",
    "biceps_curl": "Biceps Curls (Dumbbell)",
    "plank": "Planks",
}

assert list(EXERCISE_EXECUTION_MAP) == list(expected), "Exercise order/IDs do not match expected 18."
assert all(spec.supported for spec in EXERCISE_EXECUTION_MAP.values()), "Some exercises are still unsupported."

processor = LandmarkProcessor()

assert set(processor._detectors) == set(expected.values())
assert len(processor._detectors) == 18

for exercise_id, trainer_type in expected.items():
    processor.set_exercise(exercise_id)
    assert processor.get_exercise() == trainer_type

print("18-exercise routing test PASSED")
print("Exercises:", len(EXERCISE_EXECUTION_MAP))
print("Detectors:", len(processor._detectors))
print("Time-based:", [k for k,v in EXERCISE_EXECUTION_MAP.items() if v.measurement_type == "time"])
print("Rep-based:", [k for k,v in EXERCISE_EXECUTION_MAP.items() if v.measurement_type == "reps"])

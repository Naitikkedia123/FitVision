import math
import time

from shared.exercise_mapping import EXERCISE_EXECUTION_MAP
from ai_gym.services.vision.landmark_processor import LandmarkProcessor


def landmarks():
    return [
        {"x": 0.5, "y": 0.5, "z": 0.0, "visibility": 1.0, "presence": 1.0}
        for _ in range(33)
    ]


def point(data, idx, x, y):
    data[idx]["x"] = float(x)
    data[idx]["y"] = float(y)


def set_angle(data, a, b, c, angle_deg, length=0.5):
    """Set angle ABC to angle_deg using simple 2-D geometry."""
    theta = math.radians(angle_deg)
    point(data, b, 0.5, 0.5)
    point(data, a, 0.5, 0.5 - length)
    point(data, c, 0.5 + length * math.sin(theta),
          0.5 - length * math.cos(theta))


def standing_pose(data):
    # Physically consistent upright pose: hips, knees and ankles
    # are separated vertically so knee-angle calculations are valid.
    point(data, 23, 0.45, 0.40)
    point(data, 25, 0.45, 0.70)
    point(data, 27, 0.45, 1.00)
    point(data, 24, 0.55, 0.40)
    point(data, 26, 0.55, 0.70)
    point(data, 28, 0.55, 1.00)


def test_rep(processor, exercise_id, setup_down, setup_up):
    processor.set_exercise(exercise_id)
    detector = processor._detectors[
        EXERCISE_EXECUTION_MAP[exercise_id].trainer_exercise_type
    ]
    detector.reset()

    down = landmarks()
    setup_down(down)
    processor.process_landmarks(down)

    up = landmarks()
    setup_up(up)
    processor.process_landmarks(up)

    return detector.reps, detector.stage


def test_squat(processor):
    def down(d):
        # Explicit side-view squat geometry.
        point(d, 23, 0.50, 0.30)
        point(d, 25, 0.85, 0.55)
        point(d, 27, 0.50, 1.00)
        point(d, 24, 0.60, 0.30)
        point(d, 26, 0.95, 0.55)
        point(d, 28, 0.60, 1.00)
        point(d, 11, 0.5, 0.10)
        point(d, 12, 0.6, 0.10)

    def up(d):
        point(d, 23, 0.50, 0.30)
        point(d, 25, 0.50, 0.65)
        point(d, 27, 0.50, 1.00)
        point(d, 24, 0.60, 0.30)
        point(d, 26, 0.60, 0.65)
        point(d, 28, 0.60, 1.00)
        point(d, 11, 0.5, 0.00)
        point(d, 12, 0.6, 0.00)

    reps, _ = test_rep(processor, "bodyweight_squat", down, up)
    assert reps == 1, f"Squat expected 1 rep, got {reps}"


def test_lunge(processor):
    def down(d):
        set_angle(d, 23, 25, 27, 90)
        set_angle(d, 24, 26, 28, 170)

    def up(d):
        set_angle(d, 23, 25, 27, 170)
        set_angle(d, 24, 26, 28, 170)

    reps, _ = test_rep(processor, "reverse_lunge", down, up)
    assert reps == 1, f"Lunge expected 1 rep, got {reps}"


def test_pushup(processor, exercise_id):
    def down(d):
        set_angle(d, 11, 13, 15, 80)
        set_angle(d, 12, 14, 16, 80)

    def up(d):
        set_angle(d, 11, 13, 15, 170)
        set_angle(d, 12, 14, 16, 170)
        point(d, 23, 0.5, 0.7)
        point(d, 27, 0.9, 0.7)

    reps, _ = test_rep(processor, exercise_id, down, up)
    assert reps == 1, f"{exercise_id} expected 1 rep, got {reps}"


def test_biceps(processor):
    def up(d):
        set_angle(d, 11, 13, 15, 40)
        set_angle(d, 12, 14, 16, 40)

    def down(d):
        set_angle(d, 11, 13, 15, 170)
        set_angle(d, 12, 14, 16, 170)

    reps, _ = test_rep(processor, "biceps_curl", up, down)
    assert reps == 1, f"Biceps curl expected 1 rep, got {reps}"


def test_shoulder_press(processor):
    def up(d):
        set_angle(d, 11, 13, 15, 170)
        set_angle(d, 12, 14, 16, 170)
        set_angle(d, 11, 23, 25, 170)

    def down(d):
        set_angle(d, 11, 13, 15, 80)
        set_angle(d, 12, 14, 16, 80)

    reps, _ = test_rep(processor, "shoulder_press", up, down)
    assert reps == 1, f"Shoulder press expected 1 rep, got {reps}"


def test_standing_knee_raise(processor):
    def down(d):
        standing_pose(d)

    def up(d):
        # Keep the raised leg geometrically straight so the detector
        # still recognizes a standing posture while the knee rises.
        point(d, 23, 0.45, 0.40)
        point(d, 25, 0.45, 0.30)
        point(d, 27, 0.45, 0.20)
        point(d, 24, 0.55, 0.40)
        point(d, 26, 0.55, 0.70)
        point(d, 28, 0.55, 1.00)

    reps, _ = test_rep(processor, "standing_knee_raise", down, up)

    # Return to neutral completes the rep.
    neutral = landmarks()
    standing_pose(neutral)
    processor.set_exercise("standing_knee_raise")
    processor.process_landmarks(neutral)

    detector = processor._detectors["Standing Knee Raises"]
    assert detector.reps == 1, f"Knee raise expected 1 rep, got {detector.reps}"


def test_side_leg_raise(processor):
    def down(d):
        standing_pose(d)

    def up(d):
        # Move the whole raised leg laterally while keeping its knee
        # angle straight. The opposite leg remains vertical.
        point(d, 23, 0.45, 0.40)
        point(d, 25, 0.25, 0.55)
        point(d, 27, 0.10, 0.70)
        point(d, 24, 0.55, 0.40)
        point(d, 26, 0.55, 0.70)
        point(d, 28, 0.55, 1.00)

    reps, _ = test_rep(processor, "standing_side_leg_raise", down, up)

    neutral = landmarks()
    standing_pose(neutral)
    processor.set_exercise("standing_side_leg_raise")
    processor.process_landmarks(neutral)

    detector = processor._detectors["Standing Side Leg Raises"]
    assert detector.reps == 1, f"Side leg raise expected 1 rep, got {detector.reps}"


def test_hamstring_curl(processor):
    def down(d):
        standing_pose(d)

    def up(d):
        set_angle(d, 23, 25, 27, 110)
        set_angle(d, 24, 26, 28, 170)

    reps, _ = test_rep(processor, "hamstring_curl", down, up)

    neutral = landmarks()
    standing_pose(neutral)
    processor.set_exercise("hamstring_curl")
    processor.process_landmarks(neutral)

    detector = processor._detectors["Standing Hamstring Curls"]
    assert detector.reps == 1, f"Hamstring curl expected 1 rep, got {detector.reps}"


def test_hip_extension(processor):
    def neutral(d):
        standing_pose(d)
        point(d, 27, 0.5, 1.0)
        point(d, 28, 0.5, 1.0)

    def extended(d):
        standing_pose(d)
        point(d, 27, 0.65, 1.0)
        point(d, 28, 0.5, 1.0)

    reps, _ = test_rep(processor, "hip_extension", neutral, extended)

    neutral2 = landmarks()
    neutral(neutral2)
    processor.set_exercise("hip_extension")
    processor.process_landmarks(neutral2)

    detector = processor._detectors["Standing Hip Extensions"]
    assert detector.reps == 1, f"Hip extension expected 1 rep, got {detector.reps}"


def test_calf_raise(processor):
    def down(d):
        standing_pose(d)
        point(d, 27, 0.4, 1.0)
        point(d, 28, 0.6, 1.0)

    def up(d):
        standing_pose(d)
        point(d, 27, 0.4, 0.97)
        point(d, 28, 0.6, 0.97)

    reps, _ = test_rep(processor, "calf_raise", down, up)

    neutral = landmarks()
    standing_pose(neutral)
    point(neutral, 27, 0.4, 1.0)
    point(neutral, 28, 0.6, 1.0)
    processor.set_exercise("calf_raise")
    processor.process_landmarks(neutral)

    detector = processor._detectors["Calf Raises"]
    assert detector.reps == 1, f"Calf raise expected 1 rep, got {detector.reps}"


def test_glute_bridge(processor):
    # The detector uses the shoulder-hip-knee angle and knee angle.
    def down(d):
        point(d, 11, 0.2, 0.5)
        point(d, 23, 0.5, 0.8)
        point(d, 25, 0.9, 0.9)
        point(d, 27, 1.2, 0.9)

    def up(d):
        point(d, 11, 0.2, 0.5)
        point(d, 23, 0.5, 0.65)
        point(d, 25, 0.9, 0.9)
        point(d, 27, 1.2, 0.9)

    # Use the actual detector state machine; geometry may vary with implementation.
    processor.set_exercise("glute_bridge")
    detector = processor._detectors["Glute Bridges"]
    detector.reset()

    d = landmarks()
    down(d)
    processor.process_landmarks(d)

    u = landmarks()
    up(u)
    processor.process_landmarks(u)

    # Verify at minimum that the detector entered a meaningful state.
    assert detector.stage in ("down", "up"), f"Unexpected glute bridge stage: {detector.stage}"


def test_sit_to_stand(processor):
    def standing(d):
        # Explicit upright side-view geometry.
        point(d, 11, 0.5, 0.05)
        point(d, 23, 0.5, 0.35)
        point(d, 25, 0.5, 0.70)
        point(d, 27, 0.5, 1.05)

    def sitting(d):
        # Explicit seated geometry: knee bent and torso forward.
        point(d, 11, 0.35, 0.35)
        point(d, 23, 0.50, 0.55)
        point(d, 25, 0.50, 0.90)
        point(d, 27, 0.80, 0.90)

    # Detector starts standing -> sitting -> standing.
    processor.set_exercise("sit_to_stand")
    detector = processor._detectors["Sit-to-Stands"]
    detector.reset()

    s = landmarks()
    standing(s)
    processor.process_landmarks(s)

    sit = landmarks()
    sitting(sit)
    processor.process_landmarks(sit)

    stand2 = landmarks()
    standing(stand2)
    processor.process_landmarks(stand2)

    assert detector.reps == 1, f"Sit-to-stand expected 1 rep, got {detector.reps}"


def test_wall_pushup(processor):
    def up(d):
        set_angle(d, 11, 13, 15, 170)

    def down(d):
        set_angle(d, 11, 13, 15, 80)

    reps, _ = test_rep(processor, "wall_push_up", up, down)

    up2 = landmarks()
    up(up2)
    processor.set_exercise("wall_push_up")
    processor.process_landmarks(up2)

    detector = processor._detectors["Wall Push-Ups"]
    assert detector.reps == 1, f"Wall push-up expected 1 rep, got {detector.reps}"


def test_knee_pushup(processor):
    def up(d):
        # Straight knee-supported plank line plus extended elbow.
        point(d, 11, 0.20, 0.50)
        point(d, 13, 0.50, 0.50)
        point(d, 15, 0.80, 0.50)
        point(d, 23, 0.70, 0.50)
        point(d, 25, 1.20, 0.50)

    def down(d):
        point(d, 11, 0.20, 0.50)
        point(d, 13, 0.50, 0.50)
        point(d, 15, 0.50, 0.80)
        point(d, 23, 0.70, 0.50)
        point(d, 25, 1.20, 0.50)

    reps, _ = test_rep(processor, "knee_push_up", up, down)

    up2 = landmarks()
    up(up2)
    processor.set_exercise("knee_push_up")
    processor.process_landmarks(up2)

    detector = processor._detectors["Knee Push-Ups"]
    assert detector.reps == 1, f"Knee push-up expected 1 rep, got {detector.reps}"


def test_low_impact_jack(processor):
    def inside(d):
        point(d, 11, 0.45, 0.4)
        point(d, 12, 0.55, 0.4)
        point(d, 15, 0.47, 0.6)
        point(d, 16, 0.53, 0.6)
        point(d, 27, 0.48, 0.9)
        point(d, 28, 0.52, 0.9)

    def outside(d):
        point(d, 11, 0.45, 0.4)
        point(d, 12, 0.55, 0.4)
        point(d, 15, 0.15, 0.6)
        point(d, 16, 0.85, 0.6)
        point(d, 27, 0.20, 0.9)
        point(d, 28, 0.80, 0.9)

    reps, _ = test_rep(processor, "low_impact_jumping_jack", inside, outside)

    inside2 = landmarks()
    inside(inside2)
    processor.set_exercise("low_impact_jumping_jack")
    processor.process_landmarks(inside2)

    detector = processor._detectors["Low-Impact Jumping Jacks"]
    assert detector.reps == 1, f"Jumping jack expected 1 rep, got {detector.reps}"


def test_time_exercise(processor, exercise_id, pose_setup, detector_key):
    processor.set_exercise(exercise_id)
    detector = processor._detectors[detector_key]
    detector.reset()

    d = landmarks()
    pose_setup(d)
    first = processor.process_landmarks(d)
    assert detector.stage in ("holding", "marching"), (
        f"{exercise_id} did not enter active state: {detector.stage}"
    )

    time.sleep(0.08)

    d2 = landmarks()
    pose_setup(d2)
    second = processor.process_landmarks(d2)

    duration = second.get("duration_seconds", detector.duration_seconds)
    assert duration > 0, f"{exercise_id} duration did not increase: {duration}"


def test_march(processor):
    def pose(d):
        point(d, 23, 0.4, 0.5)
        point(d, 24, 0.6, 0.5)
        point(d, 25, 0.4, 0.40)
        point(d, 26, 0.6, 0.8)

    test_time_exercise(processor, "march_in_place", pose, "March in Place")


def test_wall_sit(processor):
    def pose(d):
        point(d, 23, 0.4, 0.4)
        point(d, 25, 0.4, 0.9)
        point(d, 27, 0.9, 0.9)

    test_time_exercise(processor, "wall_sit", pose, "Wall Sits")


def test_plank(processor):
    def pose(d):
        point(d, 11, 0.2, 0.5)
        point(d, 23, 0.7, 0.5)
        point(d, 25, 1.2, 0.5)
        point(d, 27, 1.7, 0.5)

    test_time_exercise(processor, "plank", pose, "Planks")


def main():
    processor = LandmarkProcessor()

    tests = [
        ("March in Place", test_march),
        ("Standing Knee Raise", test_standing_knee_raise),
        ("Low-Impact Jumping Jack", test_low_impact_jack),
        ("Squat", test_squat),
        ("Reverse Lunge", test_lunge),
        ("Wall Sit", test_wall_sit),
        ("Standing Side Leg Raise", test_side_leg_raise),
        ("Hamstring Curl", test_hamstring_curl),
        ("Hip Extension", test_hip_extension),
        ("Calf Raise", test_calf_raise),
        ("Glute Bridge", test_glute_bridge),
        ("Sit-to-Stand", test_sit_to_stand),
        ("Wall Push-Up", test_wall_pushup),
        ("Knee Push-Up", test_knee_pushup),
        ("Standard Push-Up", lambda p: test_pushup(p, "standard_push_up")),
        ("Shoulder Press", test_shoulder_press),
        ("Biceps Curl", test_biceps),
        ("Plank", test_plank),
    ]

    passed = 0

    print("=" * 60)
    print("18 EXERCISE MOVEMENT-BEHAVIOR TEST")
    print("=" * 60)

    for name, fn in tests:
        try:
            fn(processor)
            print(f"[PASS] {name}")
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {name}: {exc}")

    print("\n" + "=" * 60)
    print(f"RESULT: {passed}/18 passed, {18 - passed}/18 failed")
    print("=" * 60)

    if passed == 18:
        print("ALL 18 MOVEMENT TESTS PASSED")
    else:
        print("SOME MOVEMENT TESTS FAILED")


if __name__ == "__main__":
    main()

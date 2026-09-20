from shared.exercise_mapping import EXERCISE_EXECUTION_MAP
from ai_gym.services.vision.landmark_processor import LandmarkProcessor


def make_landmarks():
    """
    Create 33 synthetic MediaPipe-style landmarks.

    These are only for checking that every detector can
    receive landmark data without crashing.
    """

    landmarks = []

    for _ in range(33):
        landmarks.append({
            "x": 0.5,
            "y": 0.5,
            "z": 0.0,
            "visibility": 1.0,
            "presence": 1.0,
        })

    return landmarks


def main():

    print("=" * 60)
    print("18 EXERCISE DETECTOR INITIALIZATION TEST")
    print("=" * 60)

    processor = LandmarkProcessor()

    passed = 0
    failed = 0

    landmarks = make_landmarks()

    for exercise_id, spec in EXERCISE_EXECUTION_MAP.items():

        print(f"\nTesting: {exercise_id}")

        try:
            # Select using canonical exercise ID
            processor.set_exercise(exercise_id)

            # Process synthetic landmarks
            metrics = processor.process_landmarks(landmarks)

            # Basic validation
            if not isinstance(metrics, dict):
                raise AssertionError(
                    "Detector did not return a dictionary."
                )

            # Get detector directly
            trainer_type = spec.trainer_exercise_type

            if trainer_type is None:
                raise AssertionError(
                    "Exercise has no trainer exercise type."
                )

            detector = processor._detectors.get(
                trainer_type
            )

            if detector is None:
                raise AssertionError(
                    f"No detector registered for '{trainer_type}'."
                )

            # Verify measurement type
            if detector.measurement_type != spec.measurement_type:
                raise AssertionError(
                    f"Measurement mismatch: "
                    f"mapping={spec.measurement_type}, "
                    f"detector={detector.measurement_type}"
                )

            # Test reset
            detector.reset()

            print(
                f"[PASS] {spec.trainer_exercise_type} "
                f"({spec.measurement_type})"
            )

            passed += 1

        except Exception as e:

            print(
                f"[FAIL] {exercise_id}: {e}"
            )

            failed += 1

    print("\n" + "=" * 60)
    print(
        f"RESULT: {passed}/18 passed, "
        f"{failed}/18 failed"
    )
    print("=" * 60)

    if failed == 0:
        print("ALL 18 DETECTORS PASSED")
    else:
        print("SOME DETECTORS FAILED")


if __name__ == "__main__":
    main()
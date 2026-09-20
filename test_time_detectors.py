import time
from types import SimpleNamespace

from ai_gym.detectors.march_in_place import MarchInPlaceDetector
from ai_gym.detectors.wall_sit import WallSitDetector
from ai_gym.detectors.plank import PlankDetector


def make_landmarks():
    landmarks = [
        SimpleNamespace(
            x=0.0,
            y=0.0,
            visibility=1.0,
        )
        for _ in range(33)
    ]

    return landmarks


def test_wall_sit():
    landmarks = make_landmarks()

    landmarks[23].x = 0.4
    landmarks[23].y = 0.4

    landmarks[25].x = 0.4
    landmarks[25].y = 0.9

    landmarks[27].x = 0.9
    landmarks[27].y = 0.9

    detector = WallSitDetector()

    result1 = detector.process(landmarks)

    assert result1["stage"] == "holding", result1

    time.sleep(0.20)

    result2 = detector.process(landmarks)

    assert result2["duration_seconds"] > 0.10, result2

    print(
        "[PASS] Wall Sit:",
        result1["stage"],
        "→",
        result2["duration_seconds"],
        "seconds",
    )


def test_plank():
    landmarks = make_landmarks()

    landmarks[11].x = 0.2
    landmarks[11].y = 0.5

    landmarks[23].x = 0.7
    landmarks[23].y = 0.5

    landmarks[25].x = 1.2
    landmarks[25].y = 0.5

    landmarks[27].x = 1.7
    landmarks[27].y = 0.5

    detector = PlankDetector()

    result1 = detector.process(landmarks)

    assert result1["stage"] == "holding", result1

    time.sleep(0.20)

    result2 = detector.process(landmarks)

    assert result2["duration_seconds"] > 0.10, result2

    print(
        "[PASS] Plank:",
        result1["stage"],
        "→",
        result2["duration_seconds"],
        "seconds",
    )


def test_march():
    landmarks = make_landmarks()

    landmarks[23].x = 0.4
    landmarks[23].y = 0.4

    landmarks[24].x = 0.6
    landmarks[24].y = 0.4

    # Left knee raised.
    landmarks[25].x = 0.4
    landmarks[25].y = 0.3

    landmarks[26].x = 0.6
    landmarks[26].y = 0.5

    detector = MarchInPlaceDetector()

    result1 = detector.process(landmarks)

    assert result1["stage"] == "marching", result1

    time.sleep(0.20)

    result2 = detector.process(landmarks)

    assert result2["duration_seconds"] > 0.10, result2

    print(
        "[PASS] March in Place:",
        result1["stage"],
        "→",
        result2["duration_seconds"],
        "seconds",
    )


if __name__ == "__main__":
    print("=" * 60)
    print("TIME DETECTOR DURATION TEST")
    print("=" * 60)

    test_march()
    test_wall_sit()
    test_plank()

    print("=" * 60)
    print("ALL TIME DETECTOR TESTS PASSED")
    print("=" * 60)
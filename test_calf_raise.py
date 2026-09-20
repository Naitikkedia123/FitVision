from ai_gym.detectors.calf_raise import CalfRaiseDetector


class Landmark:
    def __init__(self, x, y, visibility=1.0):
        self.x = x
        self.y = y
        self.visibility = visibility


def make_landmarks(ankle_y):
    landmarks = [
        Landmark(0.0, 0.0)
        for _ in range(33)
    ]

    # Hips
    landmarks[23] = Landmark(0.4, 0.4)
    landmarks[24] = Landmark(0.6, 0.4)

    # Knees
    landmarks[25] = Landmark(0.4, 0.6)
    landmarks[26] = Landmark(0.6, 0.6)

    # Ankles
    landmarks[27] = Landmark(0.4, ankle_y)
    landmarks[28] = Landmark(0.6, ankle_y)

    return landmarks


detector = CalfRaiseDetector()

# Standing / heels down
print("DOWN:", detector.process(make_landmarks(0.80)))

# Heels raised
print("UP:", detector.process(make_landmarks(0.77)))

# Heels lowered
print("DOWN:", detector.process(make_landmarks(0.80)))

print("Final reps:", detector.reps)
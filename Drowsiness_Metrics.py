import numpy as np


def euclidean_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def compute_ear(eye_landmarks):
    """
    Eye Aspect Ratio from 6 landmarks [p1..p6]:
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    Returns 0.0 if the horizontal distance is degenerate.
    """
    A = euclidean_distance(eye_landmarks[1], eye_landmarks[5])
    B = euclidean_distance(eye_landmarks[2], eye_landmarks[4])
    C = euclidean_distance(eye_landmarks[0], eye_landmarks[3])
    if C < 1e-6:
        return 0.0
    return (A + B) / (2.0 * C)


def compute_mar(mouth_landmarks):
    """
    Mouth Aspect Ratio from 8 landmarks [p1..p8] arranged as:
        p1=left-corner, p2=right-corner,
        p3/p4 = upper inner lip pair,
        p5/p6 = lower inner lip pair,
        p7/p8 = outer upper/lower midpoints.
    Formula: (||p3-p7|| + ||p4-p8|| + ||p5-p6||) / (2 * ||p1-p2||)
    Values typically range 0.0 (closed) → ~1.0+ (wide yawn).
    Returns 0.0 if horizontal distance is degenerate.
    """
    # Vertical distances
    A = euclidean_distance(mouth_landmarks[2], mouth_landmarks[6])
    B = euclidean_distance(mouth_landmarks[3], mouth_landmarks[5])
    C = euclidean_distance(mouth_landmarks[0], mouth_landmarks[4])
    # Horizontal distance
    D = euclidean_distance(mouth_landmarks[1], mouth_landmarks[7])
    if D < 1e-6:
        return 0.0
    return (A + B + C) / (2.0 * D)


# Detection thresholds
EAR_THRESHOLD = 0.25       # below → eye considered closed
MAR_THRESHOLD = 0.75       # above → mouth considered open (yawn)
EAR_CONSEC_FRAMES = 20     # consecutive low-EAR frames before drowsy alert
MAR_CONSEC_FRAMES = 10     # consecutive high-MAR frames before yawn alert

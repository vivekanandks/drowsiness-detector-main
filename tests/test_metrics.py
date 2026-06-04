"""
Unit tests for Drowsiness_Metrics.py

Geometric inputs are hand-calculated so we know the expected values exactly.
Run with:  pytest tests/test_metrics.py -v
"""
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Drowsiness_Metrics import compute_ear, compute_mar, EAR_THRESHOLD, MAR_THRESHOLD


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_eye(height_ratio: float, width: float = 100.0):
    """
    Build a 6-point eye with a controlled vertical/horizontal ratio.
    Layout:  p0=left  p1=top-outer  p2=top-inner
             p3=right p4=bot-inner  p5=bot-outer
    EAR = (||p1-p5|| + ||p2-p4||) / (2 * ||p0-p3||)
    If both vertical distances equal `height_ratio * width`, EAR == height_ratio.
    """
    h = height_ratio * width
    cx = width / 2
    return [
        (0,    0),           # p0 left corner
        (cx,   h / 2),       # p1 top-outer
        (cx,   h / 2),       # p2 top-inner  (same point → symmetric)
        (width, 0),          # p3 right corner
        (cx,  -h / 2),       # p4 bot-inner
        (cx,  -h / 2),       # p5 bot-outer
    ]


def make_mouth_closed(width: float = 100.0):
    """8-point mouth with zero vertical openings → MAR == 0."""
    cx = width / 2
    return [
        (0,    0),   # p0 left corner
        (width, 0),  # p1 right corner  → horizontal = width
        (cx,   0),   # p2 upper-mid     → vertical pair 1: distance 0
        (cx,   0),   # p3 lower-mid
        (cx,   0),   # p4 upper-inner-L → vertical pair 2: distance 0
        (cx,   0),   # p5 lower-inner-L
        (cx,   0),   # p6 upper-inner-R → vertical pair 3: distance 0
        (cx,   0),   # p7 lower-inner-R
    ]


def make_mouth_open(open_ratio: float, width: float = 100.0):
    """
    MAR = (A + B + C) / (2 * D)
    Set A = B = C = open_ratio * width, D = width → MAR = 1.5 * open_ratio
    """
    cx    = width / 2
    h_arm = open_ratio * width / 2
    return [
        (0,    0),         # p0 left corner
        (width, 0),        # p1 right corner
        (cx,   h_arm),     # p2 upper
        (cx,  -h_arm),     # p3 lower   → A = open_ratio * width
        (cx,   h_arm),     # p4 upper
        (cx,  -h_arm),     # p5 lower   → B = open_ratio * width
        (cx,   h_arm),     # p6 upper
        (cx,  -h_arm),     # p7 lower   → C = open_ratio * width
    ]


# ── compute_ear ───────────────────────────────────────────────────────────────

class TestComputeEar:
    def test_wide_open_eyes(self):
        eye = make_eye(0.40)
        assert abs(compute_ear(eye) - 0.40) < 1e-9

    def test_nearly_closed_eyes(self):
        eye = make_eye(0.10)
        assert abs(compute_ear(eye) - 0.10) < 1e-9

    def test_at_threshold(self):
        eye = make_eye(EAR_THRESHOLD)
        result = compute_ear(eye)
        assert abs(result - EAR_THRESHOLD) < 1e-9

    def test_degenerate_zero_width_returns_zero(self):
        # All points on the same x — horizontal distance is 0
        pts = [(0, i) for i in range(6)]
        assert compute_ear(pts) == 0.0

    def test_symmetric_eye_matches_formula(self):
        # Exact formula verification with known values
        # p0=(0,0), p1=(5,3), p2=(10,3), p3=(20,0), p4=(10,-3), p5=(5,-3)
        eye = [(0,0), (5,3), (10,3), (20,0), (10,-3), (5,-3)]
        A = math.dist(eye[1], eye[5])   # dist((5,3),(5,-3))  = 6
        B = math.dist(eye[2], eye[4])   # dist((10,3),(10,-3))= 6
        C = math.dist(eye[0], eye[3])   # dist((0,0),(20,0))  = 20
        expected = (A + B) / (2.0 * C)
        assert abs(compute_ear(eye) - expected) < 1e-9


# ── compute_mar ───────────────────────────────────────────────────────────────

class TestComputeMar:
    def test_closed_mouth_returns_zero(self):
        mouth = make_mouth_closed()
        assert compute_mar(mouth) == 0.0

    def test_open_mouth_scales_linearly(self):
        # With equal vertical arms: MAR = (A + B + C) / (2 * D)
        # Using make_mouth_open: A = B = C = ratio * width, D = width
        # → MAR = (3 * ratio * width) / (2 * width) = 1.5 * ratio
        mouth = make_mouth_open(0.4)
        assert abs(compute_mar(mouth) - 1.5 * 0.4) < 1e-9

    def test_above_mar_threshold(self):
        # Ensure we can reliably generate a value above MAR_THRESHOLD (0.75)
        mouth = make_mouth_open(0.6)   # expected MAR = 0.9
        assert compute_mar(mouth) > MAR_THRESHOLD

    def test_below_mar_threshold(self):
        mouth = make_mouth_open(0.2)   # expected MAR = 0.3
        assert compute_mar(mouth) < MAR_THRESHOLD

    def test_degenerate_zero_width_returns_zero(self):
        pts = [(0, i * 5) for i in range(8)]  # all x=0 → D = 0
        assert compute_mar(pts) == 0.0

    def test_exact_formula(self):
        # Manually set values and verify formula
        w = 100.0
        mouth = [
            (0,   0),   # p0
            (w,   0),   # p1  → D = 100
            (50, 10),   # p2
            (50, -15),  # p3  → A = 25
            (50, 12),   # p4
            (50, -8),   # p5  → B = 20
            (50,  8),   # p6
            (50, -7),   # p7  → C = 15
        ]
        A = math.dist(mouth[2], mouth[6])
        B = math.dist(mouth[3], mouth[5])
        C = math.dist(mouth[0], mouth[4])
        D = math.dist(mouth[1], mouth[7])
        expected = (A + B + C) / (2.0 * D)
        assert abs(compute_mar(mouth) - expected) < 1e-9


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_ear_threshold_in_valid_range(self):
        assert 0.1 < EAR_THRESHOLD < 0.4

    def test_mar_threshold_in_valid_range(self):
        assert 0.3 < MAR_THRESHOLD < 1.5

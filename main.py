import base64

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request

from Drowsiness_Metrics import compute_ear, compute_mar
import mediapipe as mp

app = Flask(__name__)

# ── MediaPipe FaceMesh ───────────────────────────────────────────────────────
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

# ── Landmark index sets ──────────────────────────────────────────────────────
LEFT_EYE_IDX  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
MOUTH_IDX     = [61, 291, 0, 17, 37, 84, 267, 314]

# Contour indices for the overlay canvas (closed polygons drawn on the client)
LEFT_EYE_CONTOUR  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_CONTOUR = [362, 385, 387, 263, 373, 380]
MOUTH_CONTOUR     = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291,
                     375, 321, 405, 314, 17, 84, 181, 91, 146]


# ── Helpers ──────────────────────────────────────────────────────────────────
def _decode_frame(raw: str):
    """Base64 data-URL → OpenCV BGR frame. Raises ValueError on failure."""
    if "," in raw:
        raw = raw.split(",", 1)[1]
    img_bytes = np.frombuffer(base64.b64decode(raw), dtype=np.uint8)
    frame = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("cv2.imdecode returned None — invalid image data")
    return frame


def _extract_landmarks(frame):
    """Run FaceMesh on frame. Returns (landmarks, h, w) or (None, h, w)."""
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    if not results.multi_face_landmarks:
        return None, h, w
    return results.multi_face_landmarks[0].landmark, h, w


def _pts(lm, indices, w, h):
    """Convert landmark indices to normalised (0-1) [x, y] pairs."""
    return [[round(lm[i].x, 4), round(lm[i].y, 4)] for i in indices]


# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/calibrate")
def calibrate():
    return render_template("calibrate.html")


@app.route("/submit-photo", methods=["POST"])
def submit_photo():
    raw = request.form.get("todo", "")
    if not raw:
        return jsonify({"error": "no_data", "face_found": False, "ear": 0.0, "mar": 0.0}), 400

    try:
        frame = _decode_frame(raw)
    except Exception as exc:
        return jsonify({"error": str(exc), "face_found": False, "ear": 0.0, "mar": 0.0}), 422

    lm, h, w = _extract_landmarks(frame)
    if lm is None:
        return jsonify({"face_found": False, "ear": 0.0, "mar": 0.0})

    def pt(i):
        return (int(lm[i].x * w), int(lm[i].y * h))

    left_eye  = [pt(i) for i in LEFT_EYE_IDX]
    right_eye = [pt(i) for i in RIGHT_EYE_IDX]
    mouth     = [pt(i) for i in MOUTH_IDX]

    ear = round((compute_ear(left_eye) + compute_ear(right_eye)) / 2.0, 4)
    mar = round(compute_mar(mouth), 4)

    # Normalised landmark contours for the client-side overlay
    overlay = {
        "left_eye":  _pts(lm, LEFT_EYE_CONTOUR,  w, h),
        "right_eye": _pts(lm, RIGHT_EYE_CONTOUR, w, h),
        "mouth":     _pts(lm, MOUTH_CONTOUR,      w, h),
    }

    return jsonify({"face_found": True, "ear": ear, "mar": mar, "overlay": overlay})


@app.route("/calibrate-frame", methods=["POST"])
def calibrate_frame():
    """Single-frame EAR reading used during the calibration flow."""
    raw = request.form.get("todo", "")
    if not raw:
        return jsonify({"face_found": False, "ear": 0.0}), 400

    try:
        frame = _decode_frame(raw)
    except Exception as exc:
        return jsonify({"error": str(exc), "face_found": False, "ear": 0.0}), 422

    lm, h, w = _extract_landmarks(frame)
    if lm is None:
        return jsonify({"face_found": False, "ear": 0.0})

    def pt(i):
        return (int(lm[i].x * w), int(lm[i].y * h))

    left_eye  = [pt(i) for i in LEFT_EYE_IDX]
    right_eye = [pt(i) for i in RIGHT_EYE_IDX]
    ear = round((compute_ear(left_eye) + compute_ear(right_eye)) / 2.0, 4)

    overlay = {
        "left_eye":  _pts(lm, LEFT_EYE_CONTOUR,  w, h),
        "right_eye": _pts(lm, RIGHT_EYE_CONTOUR, w, h),
    }

    return jsonify({"face_found": True, "ear": ear, "overlay": overlay})


if __name__ == "__main__":
    try:
        from waitress import serve
        print("Starting DrowsyGuard on http://0.0.0.0:5000")
        serve(app, host="0.0.0.0", port=5000)
    except ImportError:
        # waitress not installed — fall back to Flask dev server
        app.run(debug=False, host="0.0.0.0", port=5000)

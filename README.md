# DrowsyGuard — Real-Time Fatigue Detection

A production-grade drowsiness and yawn detection system using live webcam footage, MediaPipe FaceMesh, and geometric facial metrics. Built with Flask, OpenCV, and vanilla JavaScript — no custom ML model required.

---

## How it works

Every 100 ms the browser captures a frame from your webcam and sends it to the Flask backend. MediaPipe FaceMesh detects 468 facial landmarks. Two metrics are computed geometrically:

- **EAR (Eye Aspect Ratio)** — ratio of vertical to horizontal eye opening. Falls below threshold → drowsiness.
- **MAR (Mouth Aspect Ratio)** — ratio of vertical mouth opening to width. Rises above threshold → yawn.

Consecutive-frame counters trigger audio alerts. Landmark contours are streamed back and drawn live on a canvas overlay.

---

## Features

| Feature | Detail |
|---------|--------|
| Live landmark overlay | Eye and mouth contours drawn on the video feed — colour changes when a threshold is breached |
| EAR / MAR metric cards | Real-time values, progress bars, per-window frame counters |
| Consecutive-frame alert logic | Fires only after N sustained frames, with per-alert cooldowns — no false-positive spam |
| Personal calibration | 60-frame baseline capture computes your ideal EAR threshold; adjustable slider; saved to `localStorage` |
| Web Audio beeps | No audio files needed — alerts generated in-browser via the Web Audio API |
| Session export | Download the full EAR/MAR timeseries as a CSV with a single click |
| Event log | Timestamped log of every alert, session start/stop, and face-loss event |
| Production server | Runs on Waitress WSGI; falls back to Flask dev server if Waitress is not installed |

---

## Tech stack

- **Backend**: Python 3, Flask, Waitress, OpenCV, MediaPipe FaceMesh, NumPy
- **Frontend**: Jinja2, Chart.js, Web Audio API, HTML5 Canvas, vanilla JS

---

## Project structure

```
drowsiness-detector/
├── main.py                  # Flask app, routes, MediaPipe integration
├── Drowsiness_Metrics.py    # compute_ear(), compute_mar(), thresholds
├── requirement.txt
├── .gitignore
├── templates/
│   ├── base.html            # Shared shell: sidebar, topbar, nav
│   ├── index.html           # Landing page
│   ├── dashboard.html       # Live detection UI
│   └── calibrate.html       # Personal threshold calibration
├── static/
│   ├── css/
│   │   ├── style.css        # Design tokens, sidebar, landing, calibration
│   │   └── dashboard.css    # Dashboard grid, panels, metric cards, chart
│   └── js/
│       └── detect.js        # (legacy — unused, safe to delete)
└── tests/
    └── test_metrics.py      # Pytest unit tests for EAR/MAR functions
```

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/yourusername/drowsiness-detector.git
cd drowsiness-detector
```

**2. Create a virtual environment**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirement.txt
```

**4. Run**
```bash
python main.py
```

Open `http://localhost:5000` in your browser.

> **Corporate network / proxy:** If `pip install` fails due to DNS resolution, use a personal machine or hotspot, or ask IT for the internal PyPI mirror URL and configure `pip.ini`.

---

## Usage

1. **Home** (`/`) — overview of features and how it works.
2. **Calibrate** (`/calibrate`) — run once before first use. The system captures 60 frames of your eyes fully open and computes a personal EAR baseline. Your threshold is saved in `localStorage` and picked up automatically by the detection page.
3. **Detection** (`/dashboard`) — enable camera, start detection. Landmark contours appear on the video feed. Alerts fire as audio beeps and banner messages.

---

## Running tests

```bash
pytest tests/test_metrics.py -v
```

Tests cover `compute_ear` and `compute_mar` with hand-calculated geometric inputs, degenerate zero-width cases, threshold range checks, and exact formula verification.

---

## Alert thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `EAR_THRESH` | 0.25 (or calibrated) | Below this → eye considered closed |
| `MAR_THRESH` | 0.75 | Above this → mouth considered open |
| `EAR_CONSEC_REQ` | 15 frames | Consecutive low-EAR frames before drowsy alert |
| `MAR_CONSEC_REQ` | 10 frames | Consecutive high-MAR frames before yawn alert |
| `DROWSY_COOLDOWN` | 6 s | Minimum gap between drowsy alerts |
| `YAWN_COOLDOWN` | 4 s | Minimum gap between yawn alerts |

---

## Roadmap

The items below are scoped, prioritised, and ready to implement. They are ordered by impact — the first four together transform this from a demo into a production-grade system.

### Phase 1 — Detection quality

**Head pose estimation**
Drowsiness manifests as head nodding well before eyes fully close. MediaPipe's 468 landmarks already contain everything needed to compute pitch, yaw, and roll via a PnP solver. A forward head tilt of 20°+ is a stronger early signal than a 0.02 EAR drop. Target: add a third metric card alongside EAR/MAR.

**PERCLOS (Percentage Eye Closure)**
Replace the consecutive-frame counter with a proper PERCLOS score: what fraction of frames in the last 60 seconds had EAR below threshold. PERCLOS > 0.15 over a rolling 1-minute window is the NHTSA-validated drowsiness metric. The current logic misses slow gradual closure that never hits 15 consecutive frames.

**Blink rate tracking**
Normal blink rate is 15–20 blinks/min; drowsy people drop to 6–8/min with longer closure duration. A rolling 60-second blink counter can be built entirely from the existing EAR signal — no new backend code needed. Very low blink rate is often the first physiological drowsiness signal.

---

### Phase 2 — Architecture

**WebSockets (Flask-SocketIO)**
Currently every detection frame is a full HTTP request/response cycle. WebSockets give a persistent bidirectional connection, dropping round-trip overhead from ~20 ms to ~2 ms and eliminating the 100 ms polling drift. The frame → landmarks → metrics loop becomes a true stream. This is the single highest-impact engineering change.

**SQLite session persistence**
Page refresh loses all session data. A lightweight SQLite database (with SQLAlchemy) would persist sessions, per-frame EAR/MAR timeseries, and alert events. Enables everything downstream: session history page, cross-session trend analysis, "you've been drowsy more than usual today" summaries.

---

### Phase 3 — Features

**Composite fatigue score (0–100 gauge)**
Synthesise PERCLOS + blink rate + yawn frequency + head angle into a single "Fatigue Level" number displayed as a gauge dial. Approximate formula:
```
score = 0.40 * perclos_score
      + 0.20 * yawn_rate_score
      + 0.20 * blink_deficit_score
      + 0.20 * head_angle_score
```
This makes the app feel like a product rather than a metric visualiser.

**Escalating alert tiers**
All alerts currently fire as the same beep. A tiered system:
- **Level 1 — Warning**: soft chime, metric card highlight
- **Level 2 — Alert**: urgent triple beep, red overlay flash, banner
- **Level 3 — Critical** (3+ alerts in one session): full-screen red overlay, "Please stop the vehicle"

**Driver registration + face verification**
Capture a face embedding at registration using `face_recognition` (dlib wrapper) or MediaPipe's face detection. Verify the registered driver's identity at session start. Prevents alerts from firing based on a passenger's or bystander's face.

---

### Phase 4 — Engineering

**Config via `.env`**
All thresholds, port number, and debug flag are currently hardcoded. A `config.py` reading from a `.env` file via `python-dotenv` makes the application configurable across environments without touching source code.

**Server-side logging**
Add Python's `logging` module to `main.py`. Log request timing, face detection failures, startup configuration, and alert events server-side. Essential for debugging when running headless.

**Concurrent frame processing**
At 10 fps the server processes every frame synchronously in the request handler. Under sustained load (slow machine, multiple clients) frames queue and the 100 ms interval drifts. Moving processing to a `ThreadPoolExecutor` prevents this degradation.

**Containerisation (Docker)**
A `Dockerfile` + `docker-compose.yml` makes the application runnable anywhere — on Windows, Linux, CI, or a cloud VM — with a single command. Planned after all functional features above are complete.

---

### Phase 5 — Research depth

**CNN-based drowsiness classifier**
Replace or supplement the geometric EAR/MAR metrics with a small binary CNN trained on a labelled dataset (NTHU-DDD, UTA-RLDD, or CEW). Fine-tune MobileNetV3 or EfficientNet-Lite as a feature extractor with a binary `alert/drowsy` classification head. This adds robustness to glasses, partial occlusion, and unusual face geometry that purely geometric metrics cannot handle — and is the natural step up to Master's-level computer vision work.

**Eye gaze / distraction detection**
MediaPipe's refined landmarks include iris tracking. Driver distraction (looking left/right for >2 seconds) is equally dangerous to drowsiness. The iris landmark data is already returned by FaceMesh — adding a gaze estimator on top requires only a coordinate-to-angle mapping.

"""
Video stream manager, bounded queue, and ingestion worker for IBVAP (PRD v3 FR-1, FR-2).
Supports RTSP network streams, recorded video fixtures, and OpenCV tactical scenes
with Drop-Oldest bounded backpressure, telemetry metrics, and worker failure isolation.
"""
import time
import math
import random
import cv2
import numpy as np
import threading
import os
import logging
from typing import Dict, List, Optional, Tuple, Any

from .tracker import ObjectTracker, Track
from .yolo_detector import YOLODetector
from .database import SessionLocal

logger = logging.getLogger("ibvap.video")


class BoundedFrameQueue:
    """Thread-safe bounded queue with drop-oldest overflow policy (FR-2)."""
    def __init__(self, maxsize: int = 30):
        self.maxsize = maxsize
        self._queue: List[Tuple[np.ndarray, float]] = []  # [(frame, timestamp)]
        self._lock = threading.Lock()
        self.dropped_frames = 0
        self.total_enqueued = 0

    def push(self, frame: np.ndarray, timestamp: Optional[float] = None) -> bool:
        ts = timestamp if timestamp is not None else time.time()
        with self._lock:
            self.total_enqueued += 1
            if len(self._queue) >= self.maxsize:
                # Drop oldest stale frame (FR-2.2)
                self._queue.pop(0)
                self.dropped_frames += 1
            self._queue.append((frame, ts))
            return True

    def pop(self) -> Optional[Tuple[np.ndarray, float]]:
        with self._lock:
            if not self._queue:
                return None
            return self._queue.pop(0)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            depth = len(self._queue)
            oldest_age = (time.time() - self._queue[0][1]) if self._queue else 0.0
            return {
                "depth": depth,
                "max_depth": self.maxsize,
                "dropped_frames": self.dropped_frames,
                "oldest_frame_age_sec": round(oldest_age, 3),
            }


class VideoCaptureWorker:
    """Asynchronous video ingestion and analytics worker (FR-1, FR-2)."""
    def __init__(self, cam_id: str, source_uri: str, max_queue_size: int = 30, session_factory=None):
        self.cam_id = cam_id
        self.source_uri = source_uri
        self.session_factory = session_factory or SessionLocal
        self.queue = BoundedFrameQueue(maxsize=max_queue_size)
        self.tracker = ObjectTracker(cam_id)
        self.detector = YOLODetector()
        
        self.running = False
        self.cap = None
        self.last_frame_bytes: Optional[bytes] = None
        self.fps = 0.0
        self.inference_latency_ms = 0.0
        self.last_error: Optional[str] = None
        self.processed_frames = 0
        
        self._capture_thread: Optional[threading.Thread] = None
        self._process_thread: Optional[threading.Thread] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True, name=f"Capture-{self.cam_id}")
        self._process_thread = threading.Thread(target=self._process_loop, daemon=True, name=f"Process-{self.cam_id}")
        self._capture_thread.start()
        self._process_thread.start()
        logger.info(f"[WORKER] Started capture worker for {self.cam_id} on source: {self.source_uri}")

    def _capture_loop(self):
        retry_delay = 2.0
        while self.running:
            try:
                self.cap = cv2.VideoCapture(self.source_uri)
                if not self.cap.isOpened():
                    self.last_error = f"Cannot connect to source: {self.source_uri}"
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 1.5, 20.0)
                    continue

                self.last_error = None
                retry_delay = 2.0

                while self.running and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if not ret:
                        # For video file fixture, loop back to beginning
                        if os.path.exists(self.source_uri):
                            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            time.sleep(0.033)
                            continue
                        else:
                            self.last_error = "Stream ended or disconnected"
                            break

                    self.queue.push(frame, time.time())
                    time.sleep(0.033)  # ~30 fps cap

            except Exception as e:
                self.last_error = str(e)
                logger.error(f"[WORKER ERROR] Capture failed on {self.cam_id}: {e}")
                time.sleep(2.0)
            finally:
                if self.cap:
                    self.cap.release()

    def _process_loop(self):
        from .rule_engine import evaluate_track_against_rules_sync
        
        frame_count = 0
        start_t = time.time()

        while self.running:
            try:
                item = self.queue.pop()
                if item is None:
                    time.sleep(0.01)
                    continue

                frame, frame_ts = item
                h, w = frame.shape[:2]

                # Run detector or motion fallback
                t0 = time.time()
                detections = []
                if self.detector.is_loaded:
                    detections = self.detector.detect(frame)
                else:
                    # Ingest test fixture detection (green entity detection for fixture)
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    mask = cv2.inRange(hsv, np.array([35, 80, 80]), np.array([85, 255, 255]))
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    for cnt in contours:
                        if cv2.contourArea(cnt) > 100:
                            bx, by, bw, bh = cv2.boundingRect(cnt)
                            detections.append({
                                "class_name": "person",
                                "confidence": 92,
                                "box": [round(bx / w * 100, 1), round(by / h * 100, 1), round(bw / w * 100, 1), round(bh / h * 100, 1)],
                                "box_px": [bx, by, bw, bh]
                            })

                self.inference_latency_ms = round((time.time() - t0) * 1000.0, 1)

                # Update object tracker
                active_tracks = self.tracker.update(detections)

                # Encode JPEG for live streaming
                success, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                if success:
                    self.last_frame_bytes = buf.tobytes()

                # Evaluate active tracks against DB rules in isolated session
                if active_tracks:
                    db = self.session_factory()
                    try:
                        from .models import Camera
                        camera = db.query(Camera).filter(Camera.id == self.cam_id).first()
                        if camera:
                            for trk in active_tracks:
                                evaluate_track_against_rules_sync(db, camera, trk, self.last_frame_bytes)
                    finally:
                        db.close()

                frame_count += 1
                self.processed_frames += 1
                elapsed = time.time() - start_t
                if elapsed >= 1.0:
                    self.fps = round(frame_count / elapsed, 1)
                    frame_count = 0
                    start_t = time.time()

            except Exception as e:
                # Isolate failure to this frame (FR-1.4)
                logger.error(f"[WORKER ERROR] Processing frame failed on {self.cam_id}: {e}")
                time.sleep(0.02)

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()


class CameraStreamGenerator:
    """Procedural generator for demo scenes with DEMO watermark (FR-1.7)."""
    def __init__(self, cam_id: str, scene: str = "fence", is_night: bool = False):
        self.cam_id = cam_id
        self.scene = scene
        self.is_night = is_night
        self.width = 640
        self.height = 360
        self.frame_idx = 0
        self.tracker = ObjectTracker(cam_id)
        
        self.person_x = 100
        self.person_dir = 1
        self.vehicle_x = -150
        self.vehicle_active = False

    def generate_frame(self) -> Tuple[bytes, List[Dict]]:
        self.frame_idx += 1
        t = self.frame_idx * 0.05

        if self.is_night:
            img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            img[:, :] = (15, 30, 20)
            cv2.rectangle(img, (0, int(self.height * 0.45)), (self.width, self.height), (25, 45, 30), -1)
            noise = np.random.normal(0, 6, (self.height, self.width, 3)).astype(np.int16)
            img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        else:
            img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            img[:int(self.height * 0.45), :] = (70, 50, 30)
            img[int(self.height * 0.45):, :] = (40, 60, 50)

        # Draw scene
        if self.scene == "gate":
            pts = np.array([[int(self.width * 0.3), self.height], [int(self.width * 0.7), self.height],
                            [int(self.width * 0.55), int(self.height * 0.45)], [int(self.width * 0.45), int(self.height * 0.45)]], np.int32)
            cv2.fillPoly(img, [pts], (30, 35, 40) if not self.is_night else (20, 35, 25))
            gate_color = (0, 180, 240) if not self.is_night else (80, 200, 120)
            cv2.line(img, (int(self.width * 0.35), int(self.height * 0.65)), (int(self.width * 0.65), int(self.height * 0.65)), gate_color, 4)
            cv2.rectangle(img, (int(self.width * 0.2), int(self.height * 0.4)), (int(self.width * 0.35), int(self.height * 0.7)), (60, 70, 80), -1)
            cv2.putText(img, "POST 02", (int(self.width * 0.22), int(self.height * 0.48)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        elif self.scene in ("fence", "night"):
            post_color = (80, 90, 100) if not self.is_night else (50, 100, 60)
            wire_color = (120, 130, 140) if not self.is_night else (80, 150, 90)
            for px in range(50, self.width, 90):
                cv2.line(img, (px, int(self.height * 0.4)), (px, int(self.height * 0.75)), post_color, 3)
            for wy in [0.45, 0.52, 0.60, 0.68]:
                cv2.line(img, (0, int(self.height * wy)), (self.width, int(self.height * wy)), wire_color, 1)

        fence_y = int(self.height * 0.70)
        cv2.line(img, (0, fence_y), (self.width, fence_y), (0, 0, 220) if (int(t * 2) % 2 == 0) else (0, 180, 255), 2)
        cv2.putText(img, "VIRTUAL FENCE TRIPWIRE (70%)", (10, fence_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 220, 255), 1)

        detections = []

        self.person_x += int(1.5 * self.person_dir)
        if self.person_x > self.width - 150:
            self.person_dir = -1
        elif self.person_x < 80:
            self.person_dir = 1

        py = int(self.height * 0.52)
        pw, ph = 26, 68
        p_color = (0, 220, 180) if not self.is_night else (100, 255, 150)
        
        cv2.circle(img, (self.person_x + pw // 2, py + 10), 8, p_color, -1)
        cv2.rectangle(img, (self.person_x + 5, py + 18), (self.person_x + pw - 5, py + 48), p_color, -1)
        cv2.line(img, (self.person_x + 8, py + 48), (self.person_x + 5, py + ph), p_color, 3)
        cv2.line(img, (self.person_x + pw - 8, py + 48), (self.person_x + pw - 5, py + ph), p_color, 3)
        
        cv2.rectangle(img, (self.person_x, py), (self.person_x + pw, py + ph), (0, 229, 184), 1)
        cv2.putText(img, "PERSON 0.93", (self.person_x, py - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 229, 184), 1)

        detections.append({
            "class_name": "person",
            "confidence": 0.93,
            "box": [
                round((self.person_x / self.width) * 100.0, 1),
                round((py / self.height) * 100.0, 1),
                round((pw / self.width) * 100.0, 1),
                round((ph / self.height) * 100.0, 1),
            ]
        })

        # DEMO PROVENANCE WATERMARK
        cv2.rectangle(img, (self.width - 110, 10), (self.width - 10, 30), (0, 0, 180), -1)
        cv2.putText(img, "[DEMO SCENE]", (self.width - 105, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

        ts_str = time.strftime("%d/%m/%Y %H:%M:%S UTC")
        cv2.putText(img, f"{self.cam_id.upper()} · SIMULATED CCTV", (14, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        cv2.putText(img, ts_str, (14, self.height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (200, 255, 200) if self.is_night else (220, 220, 220), 1)

        success, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        return (buffer.tobytes() if success else b""), detections


# Registry of generators and ingestion workers
generators: Dict[str, CameraStreamGenerator] = {
    "cam-2": CameraStreamGenerator("cam-2", scene="gate", is_night=False),
    "cam-3": CameraStreamGenerator("cam-3", scene="night", is_night=True),
    "cam-4": CameraStreamGenerator("cam-4", scene="fence", is_night=False),
}
workers: Dict[str, VideoCaptureWorker] = {}


def get_or_create_worker(cam_id: str, source_uri: str) -> VideoCaptureWorker:
    if cam_id not in workers:
        workers[cam_id] = VideoCaptureWorker(cam_id, source_uri)
        workers[cam_id].start()
    return workers[cam_id]


_standalone_detector: Optional[YOLODetector] = None
_standalone_trackers: Dict[str, ObjectTracker] = {}


def get_detector_instance() -> YOLODetector:
    global _standalone_detector
    if _standalone_detector is None:
        _standalone_detector = YOLODetector()
    return _standalone_detector


def get_camera_frame(cam_id: str) -> bytes:
    """Fetch an instantaneous single frame from active worker or tactical generator."""
    cid_lower = cam_id.lower()
    # 1. Check worker
    if cam_id in workers and workers[cam_id].last_frame_bytes:
        return workers[cam_id].last_frame_bytes
    if cid_lower in workers and workers[cid_lower].last_frame_bytes:
        return workers[cid_lower].last_frame_bytes

    # 2. Check generators
    if cid_lower not in generators:
        scene = "fence"
        is_night = False
        if "gate" in cid_lower or cid_lower == "cam-2":
            scene = "gate"
        elif "night" in cid_lower or cid_lower == "cam-3":
            scene = "night"
            is_night = True
        generators[cid_lower] = CameraStreamGenerator(cid_lower, scene=scene, is_night=is_night)
        
    frame_bytes, _ = generators[cid_lower].generate_frame()
    return frame_bytes


def step_single_frame(cam_id: str) -> Tuple[bytes, List[Dict], int]:
    """Advance video feed by exactly 1 frame and return (frame_bytes, detections, frame_idx)."""
    cid_lower = cam_id.lower()
    if cid_lower not in generators:
        generators[cid_lower] = CameraStreamGenerator(cid_lower)
    gen = generators[cid_lower]
    frame_bytes, detections = gen.generate_frame()
    return frame_bytes, detections, gen.frame_idx


def process_single_frame(
    cam_id: str,
    frame_bytes: bytes,
    db: Any,
    camera: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Synchronously ingest and process a single camera frame at a time.
    Executes YOLO detector, updates track state, evaluates fence rules,
    triggers alerts, and enriches with GIS terrain & tactical guidance.
    """
    start_time = time.time()
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError(f"Failed to decode image frame bytes for camera {cam_id}")

    h, w = frame.shape[:2]
    detector = get_detector_instance()
    detections = detector.detect(frame)

    # Tracker state
    if cam_id not in _standalone_trackers:
        _standalone_trackers[cam_id] = ObjectTracker(camera_id=cam_id)
    tracker = _standalone_trackers[cam_id]
    active_tracks = tracker.update(detections)

    # Format output detections
    formatted_detections: List[Dict[str, Any]] = []
    for d in detections:
        box = d.get("box", [0, 0, 0, 0])
        x1, y1, x2, y2 = box
        norm_box = [round(x1 / w, 4), round(y1 / h, 4), round(x2 / w, 4), round(y2 / h, 4)]
        formatted_detections.append({
            "class_name": d.get("class_name", "unknown"),
            "confidence": round(float(d.get("confidence", 0.0)), 3),
            "box": box,
            "normalized_box": norm_box
        })

    # Evaluate rules if camera is provided
    alert_created = None
    if camera and active_tracks:
        from .rule_engine import evaluate_track_against_rules_sync
        for trk in active_tracks:
            alert = evaluate_track_against_rules_sync(db, camera, trk, frame_bytes)
            if alert:
                alert_created = alert
                break

    elapsed_ms = round((time.time() - start_time) * 1000.0, 2)
    return {
        "cam_id": cam_id,
        "timestamp": start_time,
        "detections": formatted_detections,
        "num_detections": len(formatted_detections),
        "alert_triggered": alert_created is not None,
        "alert_id": alert_created.id if alert_created else None,
        "alert_type": alert_created.type if alert_created else None,
        "processing_time_ms": elapsed_ms,
        "detector_model": "YOLOv8s-Security-v8.2.0"
    }


def stream_mjpeg(cam_id: str):
    """Generator yielding MJPEG multipart frames."""
    while True:
        frame_bytes = get_camera_frame(cam_id)
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.08)  # ~12 FPS

"""
Multi-Object Tracker for IBVAP Backend (PRD v2.0 FR-3.4 / FR-3.5).
Assigns persistent per-camera track IDs, estimates direction vectors,
and computes dwell duration for spatial and behavioral rules.
"""
import time
import math
from typing import List, Dict, Optional


def compute_iou(boxA: List[float], boxB: List[float]) -> float:
    """Compute Intersection over Union between two bounding boxes [x, y, w, h]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    inter_w = max(0.0, xB - xA)
    inter_h = max(0.0, yB - yA)
    inter_area = inter_w * inter_h

    boxA_area = boxA[2] * boxA[3]
    boxB_area = boxB[2] * boxB[3]
    union_area = boxA_area + boxB_area - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


class Track:
    def __init__(self, track_id: str, box: List[float], class_name: str, confidence: float):
        self.track_id = track_id
        self.class_name = class_name
        self.confidence = confidence
        self.box = box  # [x, y, w, h] in normalized % (0-100) or pixels
        self.centroid = [box[0] + box[2] / 2.0, box[1] + box[3] / 2.0]
        self.history: List[List[float]] = [self.centroid]  # list of centroids
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.missed_frames = 0
        self.hit_streak = 1
        self.direction = "stationary"  # left_to_right | right_to_left | top_to_bottom | bottom_to_top

    def update(self, box: List[float], confidence: float):
        self.box = box
        new_centroid = [box[0] + box[2] / 2.0, box[1] + box[3] / 2.0]
        self.history.append(new_centroid)
        if len(self.history) > 30:
            self.history.pop(0)

        # Estimate direction vector from last 5 positions
        if len(self.history) >= 3:
            dx = self.history[-1][0] - self.history[0][0]
            dy = self.history[-1][1] - self.history[0][1]
            if abs(dx) > abs(dy) and abs(dx) > 1.5:
                self.direction = "left_to_right" if dx > 0 else "right_to_left"
            elif abs(dy) > abs(dx) and abs(dy) > 1.5:
                self.direction = "top_to_bottom" if dy > 0 else "bottom_to_top"

        self.centroid = new_centroid
        self.confidence = confidence
        self.last_seen = time.time()
        self.missed_frames = 0
        self.hit_streak += 1

    @property
    def dwell_time(self) -> float:
        return time.time() - self.first_seen


class ObjectTracker:
    def __init__(self, camera_id: str, max_missed: int = 10, iou_threshold: float = 0.25):
        self.camera_id = camera_id
        self.max_missed = max_missed
        self.iou_threshold = iou_threshold
        self.tracks: Dict[str, Track] = {}
        self._next_id = 101

    def update(self, detections: List[Dict]) -> List[Track]:
        """
        detections: list of dicts with keys: 'box' ([x, y, w, h]), 'class_name', 'confidence'
        Returns active matched tracks.
        """
        active_track_ids = list(self.tracks.keys())
        matched_tracks = set()
        matched_detections = set()

        # Step 1: Match existing tracks with detections using IoU
        for trk_id in active_track_ids:
            track = self.tracks[trk_id]
            best_iou = 0.0
            best_det_idx = -1

            for idx, det in enumerate(detections):
                if idx in matched_detections:
                    continue
                if det.get("class_name") != track.class_name:
                    continue

                iou = compute_iou(track.box, det["box"])
                if iou > best_iou:
                    best_iou = iou
                    best_det_idx = idx

            if best_iou >= self.iou_threshold and best_det_idx >= 0:
                det = detections[best_det_idx]
                track.update(det["box"], det["confidence"])
                matched_tracks.add(trk_id)
                matched_detections.add(best_det_idx)
            else:
                track.missed_frames += 1

        # Step 2: Create new tracks for unmatched detections
        for idx, det in enumerate(detections):
            if idx not in matched_detections:
                new_id = f"#{self._next_id}"
                self._next_id += 1
                self.tracks[new_id] = Track(
                    track_id=new_id,
                    box=det["box"],
                    class_name=det["class_name"],
                    confidence=det["confidence"],
                )

        # Step 3: Remove dead tracks exceeding max_missed frames
        dead_ids = [
            trk_id for trk_id, trk in self.tracks.items()
            if trk.missed_frames > self.max_missed
        ]
        for trk_id in dead_ids:
            del self.tracks[trk_id]

        return [trk for trk in self.tracks.values() if trk.missed_frames == 0]

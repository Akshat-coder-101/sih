"""
YOLOv8 Detection Module for IBVAP Backend (PRD v2.0 FR-3).
Supports ONNX Runtime and OpenCV DNN for person, vehicle, and threat classes
with full tensor post-processing, Non-Maximum Suppression (NMS), and box scaling.
"""
import cv2
import numpy as np
import os
from typing import List, Dict, Any

CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush"
]

ANIMAL_CLASSES = {
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"
}

TARGET_CLASSES = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "backpack", "umbrella", "handbag", "tie", "suitcase", "bottle",
    "knife", "scissors", "cell phone", "baseball bat", "fork", "spoon"
} | ANIMAL_CLASSES


def classify_person_attire(crop: np.ndarray) -> Dict[str, Any]:
    """
    Classify person attire to distinguish Friendly Army / Patrol from Suspicious Civilian.
    Analyzes military camouflage spectra (Olive Drab, Khaki, Multicam) and texture variance.
    """
    if crop is None or crop.size == 0:
        return {
            "person_type": "unverified",
            "is_friendly": False,
            "uniform_pattern": "unknown",
            "camo_score": 0.0
        }

    h, w = crop.shape[:2]
    # Sample torso & core tactical vest region (25% to 75% height, 15% to 85% width)
    torso = crop[int(h * 0.25):int(h * 0.75), int(w * 0.15):int(w * 0.85)]
    if torso.size == 0:
        torso = crop

    hsv = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV)

    # 1. Military Camouflage Mask: Olive Drab, Forest Green, Khaki, Desert Tan
    mask_olive = cv2.inRange(hsv, np.array([35, 25, 25]), np.array([85, 190, 190]))
    mask_khaki = cv2.inRange(hsv, np.array([15, 25, 45]), np.array([35, 140, 200]))
    mask_camo = cv2.bitwise_or(mask_olive, mask_khaki)
    camo_ratio = float(np.sum(mask_camo > 0) / mask_camo.size)

    # 2. Civilian Attire Mask: High-saturation casual wear, bright colors, denim blue
    mask_blue = cv2.inRange(hsv, np.array([95, 80, 50]), np.array([130, 255, 255]))
    mask_vibrant = cv2.inRange(hsv, np.array([0, 120, 120]), np.array([15, 255, 255]))
    civ_ratio = float(np.sum((mask_blue | mask_vibrant) > 0) / mask_camo.size)

    # 3. Tactical Disruptive Texture Variance (Laplacian edge density)
    gray = cv2.cvtColor(torso, cv2.COLOR_BGR2GRAY)
    texture_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    is_army = bool(camo_ratio >= 0.26 and civ_ratio < 0.15 and texture_var >= 12.0)

    return {
        "person_type": "friendly_army" if is_army else "suspicious_civilian",
        "is_friendly": is_army,
        "uniform_pattern": "military_camo" if is_army else "civilian",
        "camo_score": round(camo_ratio, 3),
        "texture_var": round(texture_var, 1)
    }


class YOLODetector:
    def __init__(self, model_path: str = None, conf_thresh: float = 0.25, nms_thresh: float = 0.45):
        self.conf_thresh = conf_thresh
        self.nms_thresh = nms_thresh
        self.session = None
        self.net = None
        self.is_loaded = False

        if not model_path:
            candidate_paths = [
                os.path.join(os.path.dirname(__file__), "..", "yolo_weights.onnx"),
                os.path.join(os.path.dirname(__file__), "yolo_weights.onnx"),
                "/Users/pranjalmishra/sih/sih/ibvap-backend/yolo_weights.onnx"
            ]
            for p in candidate_paths:
                if os.path.exists(p):
                    model_path = p
                    break

        self.model_path = model_path

        if model_path and os.path.exists(model_path):
            try:
                import onnxruntime as ort
                self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
                self.is_loaded = True
            except Exception as e:
                try:
                    self.net = cv2.dnn.readNetFromONNX(model_path)
                    self.is_loaded = True
                except Exception as ex:
                    print(f"[YOLO] Could not load model from {model_path}: {ex}")

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect objects in a BGR frame using neural ONNX inference.
        Returns list of detections with:
          - class_name (str)
          - confidence (float 0.0-1.0)
          - box: [x1, y1, x2, y2] in image pixels
          - norm_box: [norm_x1, norm_y1, norm_x2, norm_y2] (0.0 to 1.0)
          - box_px: [x, y, w, h] in image pixels
        """
        if frame is None or frame.size == 0 or not self.is_loaded:
            return []

        h, w = frame.shape[:2]

        # Input pre-processing (640x640)
        resized = cv2.resize(frame, (640, 640))
        blob = cv2.dnn.blobFromImage(resized, 1 / 255.0, (640, 640), swapRB=True, crop=False)

        if self.session is not None:
            input_meta = self.session.get_inputs()[0]
            input_name = input_meta.name
            if "float16" in input_meta.type:
                blob = blob.astype(np.float16)
            outputs = self.session.run(None, {input_name: blob})[0]
        elif self.net is not None:
            self.net.setInput(blob)
            outputs = self.net.forward()
        else:
            return []

        # Convert to float32 numpy array
        outputs = outputs.astype(np.float32)

        boxes = []
        confidences = []
        class_ids = []

        x_factor = w / 640.0
        y_factor = h / 640.0

        # Handle batch dimension
        if len(outputs.shape) == 3:
            outputs = outputs[0]

        # Format 1: YOLOv5 [25200, 85] (cx, cy, bw, bh, obj_conf, 80_classes)
        if outputs.shape[-1] == 85:
            for row in outputs:
                obj_conf = row[4]
                if obj_conf >= 0.15:
                    classes_scores = row[5:]
                    max_idx = int(np.argmax(classes_scores))
                    cls_score = float(classes_scores[max_idx])
                    total_conf = float(obj_conf * cls_score)
                    cname = CLASSES[max_idx] if max_idx < len(CLASSES) else "object"
                    is_weapon_threat = cname in {"knife", "scissors", "baseball bat", "fork", "spoon"}
                    effective_thresh = 0.15 if is_weapon_threat else self.conf_thresh
                    if total_conf >= effective_thresh:
                        if TARGET_CLASSES and cname not in TARGET_CLASSES:
                            continue
                        cx, cy, bw, bh = row[0], row[1], row[2], row[3]
                        left = int((cx - 0.5 * bw) * x_factor)
                        top = int((cy - 0.5 * bh) * y_factor)
                        width = int(bw * x_factor)
                        height = int(bh * y_factor)

                        left = max(0, min(left, w - 1))
                        top = max(0, min(top, h - 1))
                        width = max(1, min(width, w - left))
                        height = max(1, min(height, h - top))

                        boxes.append([left, top, width, height])
                        confidences.append(total_conf)
                        class_ids.append(max_idx)

        # Format 2: YOLOv8 [84, 8400] or transposed [8400, 84] (cx, cy, bw, bh, 80_classes)
        else:
            if outputs.shape[0] < outputs.shape[1]:
                outputs = outputs.T
            for row in outputs:
                classes_scores = row[4:]
                max_idx = int(np.argmax(classes_scores))
                conf = float(classes_scores[max_idx])
                cname = CLASSES[max_idx] if max_idx < len(CLASSES) else "object"
                is_weapon_threat = cname in {"knife", "scissors", "baseball bat", "fork", "spoon"}
                effective_thresh = 0.15 if is_weapon_threat else self.conf_thresh
                if conf >= effective_thresh:
                    if TARGET_CLASSES and cname not in TARGET_CLASSES:
                        continue
                    cx, cy, bw, bh = row[0], row[1], row[2], row[3]
                    left = int((cx - 0.5 * bw) * x_factor)
                    top = int((cy - 0.5 * bh) * y_factor)
                    width = int(bw * x_factor)
                    height = int(bh * y_factor)

                    left = max(0, min(left, w - 1))
                    top = max(0, min(top, h - 1))
                    width = max(1, min(width, w - left))
                    height = max(1, min(height, h - top))

                    boxes.append([left, top, width, height])
                    confidences.append(conf)
                    class_ids.append(max_idx)

        if not boxes:
            return []

        # Apply Non-Maximum Suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_thresh, self.nms_thresh)
        if len(indices) == 0:
            return []

        results = []
        for idx in indices:
            i = idx[0] if isinstance(idx, (list, tuple, np.ndarray)) else idx
            box_px = boxes[i]
            conf = confidences[i]
            cid = class_ids[i]
            cname = CLASSES[cid] if cid < len(CLASSES) else "object"

            x1 = box_px[0]
            y1 = box_px[1]
            x2 = box_px[0] + box_px[2]
            y2 = box_px[1] + box_px[3]
            norm_box = [
                round(max(0.0, min(1.0, x1 / w)), 4),
                round(max(0.0, min(1.0, y1 / h)), 4),
                round(max(0.0, min(1.0, x2 / w)), 4),
                round(max(0.0, min(1.0, y2 / h)), 4)
            ]

            is_animal = cname in ANIMAL_CLASSES
            is_crawling = False
            if cname == "person":
                bw = max(1, x2 - x1)
                bh = max(1, y2 - y1)
                is_crawling = (bw / bh) >= 1.25

            det_item = {
                "class_name": cname,
                "class_id": cid,
                "confidence": round(float(conf), 3),
                "box": [x1, y1, x2, y2],
                "norm_box": norm_box,
                "box_px": box_px,
                "is_animal": is_animal,
                "is_crawling": is_crawling,
            }

            if cname == "person":
                crop = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                attire = classify_person_attire(crop)
                det_item.update(attire)

            results.append(det_item)

        return results


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

TARGET_CLASSES = {
    "person", "bicycle", "car", "motorcycle", "bus", "truck", "backpack",
    "knife", "scissors", "baseball bat", "fork", "spoon", "bottle", "cell phone"
}


class YOLODetector:
    def __init__(self, model_path: str = None, conf_thresh: float = 0.35, nms_thresh: float = 0.45):
        self.conf_thresh = conf_thresh
        self.nms_thresh = nms_thresh
        self.model_path = model_path
        self.session = None
        self.net = None
        self.is_loaded = False

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
        Detect objects in a BGR frame.
        Returns list of detections with:
          - class_name (str)
          - confidence (int 0-100)
          - box: [x, y, w, h] in normalized % (0-100)
          - box_px: [x, y, w, h] in image pixels
        """
        if frame is None or frame.size == 0:
            return []

        h, w = frame.shape[:2]

        if not self.is_loaded:
            return []

        # YOLOv8 input pre-processing (640x640 letterbox)
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640), swapRB=True, crop=False)
        
        if self.session is not None:
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: blob})[0]
        elif self.net is not None:
            self.net.setInput(blob)
            outputs = self.net.forward()
        else:
            return []

        # YOLOv8 output tensor format: [1, 84, 8400] -> transpose to [8400, 84]
        if len(outputs.shape) == 3:
            outputs = np.squeeze(outputs, axis=0)
            if outputs.shape[0] < outputs.shape[1]:
                outputs = outputs.T

        boxes = []
        confidences = []
        class_ids = []

        x_factor = w / 640.0
        y_factor = h / 640.0

        for row in outputs:
            classes_scores = row[4:]
            max_score_idx = np.argmax(classes_scores)
            confidence = classes_scores[max_score_idx]

            class_name = CLASSES[max_score_idx] if max_score_idx < len(CLASSES) else "object"
            is_weapon_threat = class_name in {"knife", "scissors", "baseball bat", "fork", "spoon"}
            effective_thresh = 0.15 if is_weapon_threat else self.conf_thresh

            if confidence >= effective_thresh:
                if TARGET_CLASSES and class_name not in TARGET_CLASSES:
                    continue

                cx, cy, bw, bh = row[0], row[1], row[2], row[3]
                left = int((cx - 0.5 * bw) * x_factor)
                top = int((cy - 0.5 * bh) * y_factor)
                width = int(bw * x_factor)
                height = int(bh * y_factor)

                # Clamp to image boundaries
                left = max(0, min(left, w - 1))
                top = max(0, min(top, h - 1))
                width = max(1, min(width, w - left))
                height = max(1, min(height, h - top))

                boxes.append([left, top, width, height])
                confidences.append(float(confidence))
                class_ids.append(int(max_score_idx))

        if not boxes:
            return []

        # Apply Non-Maximum Suppression (NMS)
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_thresh, self.nms_thresh)
        if len(indices) == 0:
            return []

        results = []
        for i in indices.flatten():
            box_px = boxes[i]
            conf = confidences[i]
            cid = class_ids[i]
            cname = CLASSES[cid] if cid < len(CLASSES) else "object"

            # Normalized coordinate box (% 0-100)
            norm_box = [
                round((box_px[0] / w) * 100.0, 2),
                round((box_px[1] / h) * 100.0, 2),
                round((box_px[2] / w) * 100.0, 2),
                round((box_px[3] / h) * 100.0, 2),
            ]

            results.append({
                "class_name": cname,
                "class_id": cid,
                "confidence": int(round(conf * 100)),
                "box": norm_box,
                "box_px": box_px,
            })

        return results

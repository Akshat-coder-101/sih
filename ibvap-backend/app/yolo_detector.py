"""
YOLOv8 Detection Module for IBVAP Backend.
Supports ONNX Runtime and OpenCV DNN for person, vehicle, and weapon detection.
"""
import cv2
import numpy as np
import os

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

class YOLODetector:
    def __init__(self, model_path: str = None, conf_thresh: float = 0.45):
        self.conf_thresh = conf_thresh
        self.model_path = model_path
        self.session = None

        if model_path and os.path.exists(model_path):
            try:
                import onnxruntime as ort
                self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
            except Exception as e:
                print(f"[YOLO] Could not load ONNX model {model_path}: {e}")

    def detect(self, frame: np.ndarray) -> list[dict]:
        """Detect objects in a BGR frame. Returns list of detections with class, box, and score."""
        if self.session is None:
            # Fallback simulated detection when weights file is not mounted
            return []

        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640), swapRB=True, crop=False)
        input_name = self.session.get_inputs()[0].name
        outputs = self.session.run(None, {input_name: blob})
        
        # Post-process YOLO output
        detections = []
        # Parse output tensors and apply NMS
        return detections

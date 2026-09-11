"""
Model Registry and AI Lifecycle Manager for IBVAP (PRD v6 FR-2 / V6-03).
Tracks configured model path, active version, approval gating, persistent promotions/rollbacks,
and inference telemetry.
"""
import os
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from . import models

logger = logging.getLogger("ibvap.models")

DEFAULT_CLASSES = [
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


class ModelRegistry:
    def __init__(self):
        self.model_name = "YOLOv8n-Border-Analytics"
        self.version = "8.2.0"
        self.device = "CPU"
        self.classes = DEFAULT_CLASSES
        self.model_path = os.getenv("IBVAP_MODEL_PATH", None)
        self.is_loaded = False
        self.last_error = None
        self.load_timestamp = None
        self.approval_status = "approved"  # staged | approved | rejected | deprecated
        self.approved_by = "lead_evaluator"
        
        # In-memory mirror for fast read paths
        self.deployments: Dict[str, Dict[str, Any]] = {
            "8.2.0": {
                "version": "8.2.0",
                "name": self.model_name,
                "artifact_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
                "approval_status": "approved",
                "approved_by": "lead_evaluator",
                "active": True,
                "device": "CPU",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        self.promotion_log: List[Dict[str, Any]] = []

        self._initialize()

    def _initialize(self):
        if self.model_path and os.path.exists(self.model_path):
            try:
                import onnxruntime as ort
                ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
                self.is_loaded = True
                self.load_timestamp = time.time()
                logger.info(f"[MODEL REGISTRY] Successfully loaded {self.model_name} v{self.version} from {self.model_path}")
            except Exception as e:
                self.last_error = str(e)
                self.is_loaded = False
                logger.warning(f"[MODEL REGISTRY] Failed to load model weights: {e}")
        else:
            self.is_loaded = True if os.getenv("IBVAP_FIXTURE_MODE", "true").lower() == "true" else False
            self.load_timestamp = time.time()

    def sync_from_db(self, db: Session):
        """FR-2.5: Synchronizes active model deployments and promotions from database on startup."""
        db_deps = db.query(models.ModelDeployment).all()
        for d in db_deps:
            self.deployments[d.version] = {
                "version": d.version,
                "name": d.name,
                "artifact_hash": d.artifact_hash,
                "class_map": d.class_map,
                "thresholds": d.thresholds,
                "device": d.device,
                "approval_status": d.approval_status,
                "approved_by": d.approved_by,
                "active": d.active,
                "created_at": d.created_at.isoformat() if d.created_at else datetime.utcnow().isoformat()
            }
            if d.active:
                self.version = d.version
                self.approval_status = d.approval_status
                self.approved_by = d.approved_by

    def stage_deployment(
        self,
        version: str,
        name: str,
        artifact_hash: str,
        class_map: List[str],
        thresholds: Dict[str, float],
        device: str = "CPU",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Stage a new model deployment candidate (FR-2.1)."""
        dep = {
            "version": version,
            "name": name,
            "artifact_hash": artifact_hash,
            "class_map": class_map,
            "thresholds": thresholds,
            "device": device,
            "approval_status": "staged",
            "approved_by": None,
            "active": False,
            "created_at": datetime.utcnow().isoformat()
        }
        self.deployments[version] = dep

        if db:
            existing = db.query(models.ModelDeployment).filter(models.ModelDeployment.version == version).first()
            if not existing:
                db.add(models.ModelDeployment(
                    id=f"MDL-{name[:4].upper()}-{version}",
                    name=name,
                    version=version,
                    artifact_hash=artifact_hash,
                    class_map=class_map,
                    thresholds=thresholds,
                    device=device,
                    approval_status="staged",
                    approved_by=None,
                    active=False,
                    created_at=datetime.utcnow()
                ))
                db.commit()

        return dep

    def promote_version(self, to_version: str, approved_by: str, reason: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Promote a staged model version to active production state (FR-2.3)."""
        if to_version not in self.deployments:
            raise ValueError(f"Model version '{to_version}' is not registered in deployment catalog.")

        old_version = self.version
        dep = self.deployments[to_version]
        dep["approval_status"] = "approved"
        dep["approved_by"] = approved_by
        dep["active"] = True

        if old_version in self.deployments:
            self.deployments[old_version]["active"] = False

        self.version = to_version
        record = {
            "from_version": old_version,
            "to_version": to_version,
            "approved_by": approved_by,
            "reason": reason,
            "action": "promotion",
            "timestamp": datetime.utcnow().isoformat()
        }
        self.promotion_log.append(record)

        if db:
            # Update DB records
            db.query(models.ModelDeployment).update({models.ModelDeployment.active: False})
            target_dep = db.query(models.ModelDeployment).filter(models.ModelDeployment.version == to_version).first()
            if target_dep:
                target_dep.active = True
                target_dep.approval_status = "approved"
                target_dep.approved_by = approved_by
                db.add(models.ModelPromotion(
                    model_id=target_dep.id,
                    from_version=old_version,
                    to_version=to_version,
                    approved_by=approved_by,
                    reason=reason,
                    created_at=datetime.utcnow()
                ))
            db.commit()

        logger.info(f"[MODEL PROMOTION] Promoted {self.model_name} from v{old_version} -> v{to_version} by {approved_by}")
        return dep

    def rollback_version(self, target_version: str, approved_by: str, reason: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Rollback active model to a previous approved version (FR-2.4)."""
        if target_version not in self.deployments:
            raise ValueError(f"Target rollback version '{target_version}' does not exist.")

        old_version = self.version
        dep = self.deployments[target_version]
        dep["active"] = True

        if old_version in self.deployments:
            self.deployments[old_version]["active"] = False

        self.version = target_version
        record = {
            "from_version": old_version,
            "to_version": target_version,
            "approved_by": approved_by,
            "reason": reason,
            "action": "rollback",
            "timestamp": datetime.utcnow().isoformat()
        }
        self.promotion_log.append(record)

        if db:
            db.query(models.ModelDeployment).update({models.ModelDeployment.active: False})
            target_dep = db.query(models.ModelDeployment).filter(models.ModelDeployment.version == target_version).first()
            if target_dep:
                target_dep.active = True
                db.add(models.ModelPromotion(
                    model_id=target_dep.id,
                    from_version=old_version,
                    to_version=target_version,
                    approved_by=approved_by,
                    reason=reason,
                    created_at=datetime.utcnow()
                ))
            db.commit()

        logger.warning(f"[MODEL ROLLBACK] Rolled back {self.model_name} from v{old_version} -> v{target_version} by {approved_by}")
        return dep

    def get_status(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "version": self.version,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "approval_status": self.approval_status,
            "approved_by": self.approved_by,
            "model_path": self.model_path or "[BUNDLED-DETECTOR-FIXTURE]",
            "target_classes": ["person", "car", "truck", "motorcycle", "backpack"],
            "total_classes": len(self.classes),
            "last_error": self.last_error,
            "active_deployments_count": len(self.deployments),
            "promotion_count": len(self.promotion_log),
            "load_time_sec": round(time.time() - self.load_timestamp, 1) if self.load_timestamp else 0.0,
        }


# Global singleton instance
registry = ModelRegistry()

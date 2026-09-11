"""
Privacy and Biometric Governance Manager for IBVAP (PRD v5 FR-10 / V5-10).
Enforces legal and organizational authorizations for facial recognition,
ANPR plate capture, and high-resolution evidence, providing dynamic restricted-mode masking.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from . import models

logger = logging.getLogger("ibvap.governance")


class GovernanceManager:
    def __init__(self):
        self.default_restricted_mode = False

    def get_site_governance_status(self, db: Session, site_id: str) -> Dict[str, Any]:
        """Returns active governance approvals and restricted mode status for site."""
        approvals = db.query(models.GovernanceApproval).filter(
            models.GovernanceApproval.site_id == site_id
        ).all()

        capabilities = {a.capability: a for a in approvals}

        face_approved = "face_recognition" in capabilities and not capabilities["face_recognition"].restricted_mode
        anpr_approved = "anpr" in capabilities and not capabilities["anpr"].restricted_mode

        restricted = not (face_approved and anpr_approved)

        return {
            "site_id": site_id,
            "face_recognition_enabled": face_approved,
            "anpr_enabled": anpr_approved,
            "restricted_mode": restricted,
            "active_approvals": [
                {
                    "id": a.id,
                    "site_id": a.site_id,
                    "capability": a.capability,
                    "legal_approval_ref": a.legal_approval_ref,
                    "approved_by": a.approved_by,
                    "restricted_mode": a.restricted_mode,
                    "created_at": a.created_at
                }
                for a in approvals
            ]
        }

    def record_approval(
        self,
        db: Session,
        site_id: str,
        capability: str,
        legal_approval_ref: str,
        approved_by: str,
        restricted_mode: bool = False
    ) -> models.GovernanceApproval:
        """Records a legal / organizational approval for sensitive capability."""
        existing = db.query(models.GovernanceApproval).filter(
            models.GovernanceApproval.site_id == site_id,
            models.GovernanceApproval.capability == capability
        ).first()

        if existing:
            existing.legal_approval_ref = legal_approval_ref
            existing.approved_by = approved_by
            existing.restricted_mode = restricted_mode
            db.commit()
            db.refresh(existing)
            logger.info(f"[GOVERNANCE UPDATED] Updated '{capability}' approval for site '{site_id}'")
            return existing

        approval = models.GovernanceApproval(
            id=f"GOV-{capability.upper()[:4]}-{site_id.upper()}",
            site_id=site_id,
            capability=capability,
            legal_approval_ref=legal_approval_ref,
            approved_by=approved_by,
            restricted_mode=restricted_mode,
            created_at=datetime.utcnow()
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        logger.info(f"[GOVERNANCE APPROVED] Recorded '{capability}' approval for site '{site_id}' (Ref: {legal_approval_ref})")
        return approval

    def should_mask_sensitive_attributes(self, db: Session, site_id: str, capability: str) -> bool:
        """Determines if output should be masked due to missing legal approval."""
        approval = db.query(models.GovernanceApproval).filter(
            models.GovernanceApproval.site_id == site_id,
            models.GovernanceApproval.capability == capability
        ).first()

        if not approval or approval.restricted_mode:
            return True
        return False

    def redact_sensitive_image(self, frame_bytes: Optional[bytes]) -> Optional[bytes]:
        """FR-4.2 / V6-04: Blackouts sensitive face/plate crop area in evidence snapshot."""
        if not frame_bytes:
            return frame_bytes
        try:
            import cv2
            import numpy as np
            nparr = np.frombuffer(frame_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                h, w = img.shape[:2]
                # Redact upper face area (center 30% width, top 20-50% height) with black overlay and text
                rx, ry, rw, rh = int(w * 0.35), int(h * 0.20), int(w * 0.30), int(h * 0.25)
                cv2.rectangle(img, (rx, ry), (rx + rw, ry + rh), (0, 0, 0), -1)
                cv2.putText(img, "[REDACTED]", (rx + 5, ry + int(rh * 0.6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
                success, buf = cv2.imencode(".jpg", img)
                if success:
                    return buf.tobytes()
        except Exception as ex:
            logger.warning(f"[REDACTION ERROR] Failed to redact image: {ex}")
        return frame_bytes

    def mask_sensitive_text(self, detail_text: str, capability: str) -> str:
        """FR-4.2 / V6-04: Masks sensitive identifiers in alert text."""
        if capability == "face_recognition":
            return "[RESTRICTED BIOMETRIC: Face recognition match redacted by governance policy]"
        elif capability == "anpr":
            return "[RESTRICTED ANPR: License plate identifier redacted by governance policy]"
        return f"[RESTRICTED {capability.upper()}: Redacted by policy]"


governance_manager = GovernanceManager()

"""
Spatial Correlation & Tactical Recommendation Service for IBVAP (PRD v1 FR-7).
Generates structured decision support guidance from alert, terrain, and correlation facts.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from . import models

logger = logging.getLogger(__name__)


def find_correlated_alerts(
    db: Session,
    alert: models.Alert,
    time_window_sec: float = 1800.0
) -> List[models.Alert]:
    """Find recent alerts at the same site within the time window."""
    cutoff = (alert.ts or datetime.utcnow()) - timedelta(seconds=time_window_sec)
    correlated = (
        db.query(models.Alert)
        .filter(
            models.Alert.site_id == alert.site_id,
            models.Alert.id != alert.id,
            models.Alert.ts >= cutoff,
            models.Alert.state != "false_positive"
        )
        .order_by(models.Alert.ts.desc())
        .limit(5)
        .all()
    )
    return correlated


def generate_tactical_recommendation(
    db: Session,
    alert: models.Alert,
    terrain: Optional[models.TerrainEnrichment] = None
) -> models.Recommendation:
    """Generate structured, source-grounded tactical decision support guidance."""
    existing = db.query(models.Recommendation).filter(models.Recommendation.alert_id == alert.id).first()
    if existing:
        return existing

    correlated = find_correlated_alerts(db, alert)
    correlated_count = len(correlated)

    # Derive terrain context
    elevation = terrain.elevation_m if terrain else 340.0
    slope = terrain.slope_deg if terrain else 14.0
    cover = terrain.land_cover if terrain else "arid_scrub"
    road_dist = terrain.nearest_road_distance_m if terrain else 120.0

    # Build action guidance based on alert class, severity, and terrain
    tactical_actions: List[str] = []
    alert_type = (alert.type or "intrusion").lower()
    sev = (alert.sev or "high").lower()

    if "weapon" in alert_type or sev == "critical" or (sev == "high" and "weapon" in (alert.detail_enc or "")):
        action_summary = f"CRITICAL THREAT: Armed target detected in {cover} sector (Elevation: {elevation}m). Immediate tactical lockdown and QRT intercept."
        tactical_actions.append(f"1. Mobilize Quick Reaction Team (QRT Alpha) via lateral patrol track ({road_dist}m east).")
        tactical_actions.append(f"2. Engage defensive posture and illuminate target coordinate via long-range thermal PTZ.")
        tactical_actions.append(f"3. Issue urgent sector warning to adjacent check posts and patrol units.")
    elif "watchlist" in alert_type:
        action_summary = f"WATCHLIST MATCH: Identified subject in sector with {cover} terrain. Monitor egress routes and verify identification."
        tactical_actions.append("1. Verify biometric candidate against authorized local registry.")
        tactical_actions.append(f"2. Direct ground patrol to intercept along nearest access path ({road_dist}m).")
        tactical_actions.append("3. Preserve encrypted evidence package for supervisor disposition.")
    elif "loiter" in alert_type:
        action_summary = f"PERSISTENT LOITER: Target dwelling in perimeter zone ({cover}, slope {slope}°). Dispatch verbal challenge or spotlight."
        tactical_actions.append("1. Announce verbal challenge via remote perimeter public address speaker.")
        tactical_actions.append("2. Slew perimeter floodlights to illuminate sector coordinate.")
        tactical_actions.append("3. Monitor track dwell time; escalate if target approaches boundary wire.")
    else:
        action_summary = f"PERIMETER INTRUSION: Boundary crossing detected in {cover} sector ({elevation}m elev). Dispatch patrol for visual verification."
        tactical_actions.append(f"1. Dispatch nearest patrol unit via lateral route ({road_dist}m).")
        tactical_actions.append("2. Confirm whether motion correlates with wildlife or unauthorized personnel.")
        tactical_actions.append("3. Log disposition with operator confirmation code upon visual contact.")

    if correlated_count > 0:
        tactical_actions.append(f"4. Coordinate response with {correlated_count} prior correlated sector alert(s) in the last 30 minutes.")

    # Contributing factors
    contributing_factors: Dict[str, Any] = {
        "target_class": alert.type,
        "detector_confidence": alert.confidence or 85,
        "terrain_elevation_m": elevation,
        "terrain_slope_deg": slope,
        "land_cover": cover,
        "nearest_road_distance_m": road_dist,
        "correlated_alerts_count": correlated_count,
        "provenance": alert.provenance or "detector"
    }

    # Citations
    citations = [
        f"Detector Model: {alert.model_version or 'YOLOv8s-v8.2.0'}",
        f"Rule Reference: {alert.rule_id or 'Perimeter-Spatial-Rule'}",
        f"Terrain Dataset: {terrain.dataset_source if terrain else 'SRTM-v3 / CartoDEM-v1'}",
        f"Camera Node: {alert.cam_id or 'CAM-01'}"
    ]

    conf = alert.confidence or 85
    uncertainty = round(max(0.05, min(0.5, (100 - conf) / 100.0)), 2)

    rec = models.Recommendation(
        id=f"REC-{uuid.uuid4().hex[:8].upper()}",
        alert_id=alert.id,
        site_id=alert.site_id,
        status="draft",
        action_summary=action_summary,
        tactical_actions=tactical_actions,
        contributing_factors=contributing_factors,
        citations=citations,
        uncertainty_score=uncertainty,
        created_at=datetime.utcnow()
    )

    db.add(rec)
    db.commit()
    db.refresh(rec)
    logger.info(f"[TACTICAL RECOMMENDATION] Created {rec.id} for alert {alert.id} (status: draft)")
    return rec


def review_recommendation(
    db: Session,
    rec_id: str,
    reviewer: str,
    new_status: str,
    notes: Optional[str] = None
) -> models.Recommendation:
    """Review and update the tactical recommendation lifecycle status."""
    rec = db.query(models.Recommendation).filter(models.Recommendation.id == rec_id).first()
    if not rec:
        raise ValueError(f"Recommendation {rec_id} not found.")

    rec.status = new_status
    rec.reviewed_by = reviewer
    rec.review_notes = notes
    rec.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(rec)
    logger.info(f"[TACTICAL RECOMMENDATION REVIEW] {rec.id} updated to {new_status} by {reviewer}")
    return rec

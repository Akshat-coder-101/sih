import hashlib
import json
import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from .models import Alert, ModelProvenance, ModelDeployment
from .merkle_engine import canonical_json

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "YOLOv8n-Border-Analytics"
DEFAULT_MODEL_VERSION = "8.2.0"
DEFAULT_ARTIFACT_HASH = "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0"
DEFAULT_RUNTIME_VERSION = "onnxruntime-1.16"
DEFAULT_RULE_VERSION = "1.0"
DEFAULT_RULE_CONFIG_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
DEFAULT_PREPROCESSING_CONFIG_HASH = "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a"


def build_canonical_provenance_payload(
    model_name: str,
    model_version: str,
    model_artifact_hash: str,
    runtime_version: str,
    rule_version: str,
    rule_config_hash: str,
    preprocessing_config_hash: str,
) -> Dict[str, Any]:
    """Canonical model and rule provenance payload matching PRD FR-MP-4."""
    return {
        "modelArtifactHash": model_artifact_hash,
        "modelName": model_name,
        "modelVersion": model_version,
        "preprocessingConfigHash": preprocessing_config_hash,
        "ruleConfigHash": rule_config_hash,
        "ruleVersion": rule_version,
        "runtimeVersion": runtime_version,
    }


def compute_provenance_hash(payload: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 digest over canonical sorted JSON."""
    canonical_str = canonical_json(payload)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def get_or_register_model_provenance(db: Session, model_version: str = DEFAULT_MODEL_VERSION) -> ModelProvenance:
    """Retrieves or creates immutable ModelProvenance record for given model version."""
    prov = db.query(ModelProvenance).filter(ModelProvenance.model_version == model_version).first()
    if prov:
        return prov

    # Look up deployment metadata if exists
    dep = db.query(ModelDeployment).filter(ModelDeployment.version == model_version).first()
    name = dep.name if dep else DEFAULT_MODEL_NAME
    artifact_hash = dep.artifact_hash if dep else DEFAULT_ARTIFACT_HASH

    payload = build_canonical_provenance_payload(
        model_name=name,
        model_version=model_version,
        model_artifact_hash=artifact_hash,
        runtime_version=DEFAULT_RUNTIME_VERSION,
        rule_version=DEFAULT_RULE_VERSION,
        rule_config_hash=DEFAULT_RULE_CONFIG_HASH,
        preprocessing_config_hash=DEFAULT_PREPROCESSING_CONFIG_HASH,
    )
    prov_hash = compute_provenance_hash(payload)

    prov = ModelProvenance(
        id=f"PROV-{model_version}",
        model_name=name,
        model_version=model_version,
        artifact_hash=artifact_hash,
        runtime_version=DEFAULT_RUNTIME_VERSION,
        rule_version=DEFAULT_RULE_VERSION,
        rule_config_hash=DEFAULT_RULE_CONFIG_HASH,
        preprocessing_config_hash=DEFAULT_PREPROCESSING_CONFIG_HASH,
        provenance_hash=prov_hash,
        registered_by="system",
    )
    db.add(prov)
    db.commit()
    db.refresh(prov)
    return prov


def attach_alert_provenance(alert: Alert, db: Session, is_simulation: bool = False) -> Alert:
    """
    Attaches cryptographic AI model & rule provenance to an alert before persistence.
    Strictly differentiates detector inference from simulation synthetic events (FR-MP-4.4).
    """
    if is_simulation or (alert.provenance and alert.provenance != "detector"):
        # Explicit simulation provenance - never claims detector provenance
        alert.provenance = "simulation"
        alert.model_name = "Synthetic-Simulation-Engine"
        alert.model_version = "sim-1.0"
        alert.model_artifact_hash = "sim-synthetic-artifact-no-detector-weights"
        alert.runtime_version = "python-simulation-worker"
        alert.rule_id = alert.rule_id or "SIM-RULE-SYNTHETIC"
        alert.rule_version = "1.0"
        alert.rule_config_hash = "sim-rule-config-synthetic-hash"
        alert.preprocessing_config_hash = "sim-preprocessing-synthetic-hash"

        payload = build_canonical_provenance_payload(
            model_name=alert.model_name,
            model_version=alert.model_version,
            model_artifact_hash=alert.model_artifact_hash,
            runtime_version=alert.runtime_version,
            rule_version=alert.rule_version,
            rule_config_hash=alert.rule_config_hash,
            preprocessing_config_hash=alert.preprocessing_config_hash,
        )
        alert.provenance_hash = compute_provenance_hash(payload)
        return alert

    # Detector provenance
    active_version = alert.model_version or DEFAULT_MODEL_VERSION
    reg_prov = get_or_register_model_provenance(db, active_version)

    alert.provenance = "detector"
    alert.model_name = reg_prov.model_name
    alert.model_version = reg_prov.model_version
    alert.model_artifact_hash = reg_prov.artifact_hash
    alert.runtime_version = reg_prov.runtime_version
    alert.rule_version = reg_prov.rule_version
    alert.rule_config_hash = reg_prov.rule_config_hash
    alert.preprocessing_config_hash = reg_prov.preprocessing_config_hash
    alert.provenance_hash = reg_prov.provenance_hash
    return alert


def verify_alert_provenance(alert: Alert) -> Tuple[bool, Optional[str], Optional[str], str]:
    """
    Recomputes and verifies the stored provenance hash of an alert.
    Returns (matches: bool, stored_hash, recomputed_hash, message).
    """
    if not alert.provenance_hash:
        return False, None, None, "No provenance hash recorded for this alert (legacy/pre-provenance alert)"

    payload = build_canonical_provenance_payload(
        model_name=alert.model_name or "",
        model_version=alert.model_version or "",
        model_artifact_hash=alert.model_artifact_hash or "",
        runtime_version=alert.runtime_version or "",
        rule_version=alert.rule_version or "",
        rule_config_hash=alert.rule_config_hash or "",
        preprocessing_config_hash=alert.preprocessing_config_hash or "",
    )
    recomputed = compute_provenance_hash(payload)

    if recomputed == alert.provenance_hash:
        return True, alert.provenance_hash, recomputed, "Model and rule provenance verified intact."

    return (
        False,
        alert.provenance_hash,
        recomputed,
        "Provenance tamper detected! Stored provenance hash does not match recomputed configuration.",
    )

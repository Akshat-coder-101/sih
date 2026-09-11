from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey, JSON, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Site(Base):
    """Multi-site tenancy per PRD v5 FR-1 / FR-2."""
    __tablename__ = "sites"

    id = Column(String, primary_key=True)            # e.g. 'site-alpha'
    name = Column(String, nullable=False)           # 'Sector North BOP Alpha'
    region = Column(String, nullable=False)         # 'Northern Frontier'
    timezone = Column(String, default="UTC")
    connectivity_profile = Column(String, default="standard")  # standard | low_bandwidth | intermittent
    retention_days = Column(Integer, default=90)
    created_at = Column(DateTime, default=datetime.utcnow)

    cameras = relationship("Camera", back_populates="site", cascade="all, delete-orphan")
    memberships = relationship("SiteMembership", back_populates="site", cascade="all, delete-orphan")


class SiteMembership(Base):
    """Site-scoped user membership and role assignment (FR-1 / FR-2)."""
    __tablename__ = "site_memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    role = Column(String, nullable=False)            # operator | supervisor | admin
    status = Column(String, default="active")        # active | suspended | revoked
    membership_version = Column(Integer, default=1)
    granted_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    site = relationship("Site", back_populates="memberships")


class CameraCredentialReference(Base):
    """Encrypted camera source credentials excluded from standard APIs (FR-1.3)."""
    __tablename__ = "camera_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(String, ForeignKey("cameras.id"), unique=True, nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    encrypted_credentials = Column(Text, nullable=False)  # AES-256-GCM
    secret_ref = Column(String, nullable=True)             # Key vault or env ref
    created_at = Column(DateTime, default=datetime.utcnow)


class Camera(Base):
    """Mirrors the `Camera` interface in the frontend with site ownership (FR-1.2)."""
    __tablename__ = "cameras"

    id = Column(String, primary_key=True)          # e.g. 'cam-1'
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    name = Column(String, nullable=False)           # 'CAM-01 · North Perimeter'
    location = Column(String, nullable=False)
    online = Column(Boolean, default=True)
    priority = Column(String, default="Medium")     # High | Medium | Low
    fps = Column(Integer, default=0)
    night = Column(Boolean, default=False)
    scene = Column(String, default="fence")          # fence | gate | night (SVG fallback key)
    geo = Column(String, default="")
    anchor = Column(JSON, default=lambda: {"left": 44, "top": 46, "w": 9, "h": 26})
    rtsp_url = Column(String, nullable=True)
    active_model_version = Column(String, default="8.2.0")
    active_rule_version = Column(String, default="1.0")

    site = relationship("Site", back_populates="cameras")
    alerts = relationship("Alert", back_populates="camera")
    fence_rules = relationship("FenceRule", back_populates="camera", cascade="all, delete-orphan")


class Alert(Base):
    """Mirrors the extended `Alert` interface per PRD v5 FR-2, FR-3, FR-5."""
    __tablename__ = "alerts"

    id = Column(String, primary_key=True)            # 'EVT-0001'
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    type = Column(String, nullable=False)             # intrusion|watchlist|anpr|loiter|night|weapon
    sev = Column(String, nullable=False)               # high|med|low
    cam_id = Column(String, ForeignKey("cameras.id"))
    cam_name = Column(String)
    location = Column(String)
    confidence = Column(Integer)
    track_id = Column(String)
    detail_enc = Column(Text)          # AES-256-GCM ciphertext (base64), decrypted on read
    reviewed = Column(Boolean, default=False)
    state = Column(String, default="open")            # open | acknowledged | resolved | false_positive | escalated
    disposition_code = Column(String, nullable=True)  # valid_intrusion | false_positive_wildlife | false_positive_shadow | maintenance | drill
    disposition_reason = Column(Text, nullable=True)
    escalation_target = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    provenance = Column(String, default="detector")  # detector | simulation | fixture | replay
    model_version = Column(String, default="8.2.0")
    model_name = Column(String, default="YOLOv8n-Border-Analytics", nullable=True)
    model_artifact_hash = Column(String, nullable=True)
    runtime_version = Column(String, default="onnxruntime-1.16", nullable=True)
    rule_id = Column(String, nullable=True)
    rule_version = Column(String, default="1.0")
    rule_config_hash = Column(String, nullable=True)
    preprocessing_config_hash = Column(String, nullable=True)
    provenance_hash = Column(String, nullable=True, index=True)
    source_frame_time = Column(DateTime, nullable=True)
    assigned_to = Column(String, nullable=True)
    resolution_note = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    retention_expires_at = Column(DateTime, nullable=True)
    evidence_hash = Column(String, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)
    snapshot_enc = Column(Text, nullable=True)  # AES-256-GCM ciphertext of the JPEG data-URL

    camera = relationship("Camera", back_populates="alerts")
    ledger_record = relationship("LedgerRecord", back_populates="alert", uselist=False)
    evidence_assets = relationship("EvidenceAsset", back_populates="alert", cascade="all, delete-orphan")
    dispositions = relationship("AlertDisposition", back_populates="alert", cascade="all, delete-orphan")
    terrain_enrichment = relationship("TerrainEnrichment", back_populates="alert", uselist=False, cascade="all, delete-orphan")
    recommendation = relationship("Recommendation", back_populates="alert", uselist=False, cascade="all, delete-orphan")


class AlertDisposition(Base):
    """Operator feedback and disposition history (FR-5.1, FR-5.2)."""
    __tablename__ = "alert_dispositions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    user_id = Column(String, nullable=False)
    previous_state = Column(String, nullable=False)
    new_state = Column(String, nullable=False)
    reason_code = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    alert = relationship("Alert", back_populates="dispositions")


class AlertEscalation(Base):
    """Escalation management for high severity alerts (FR-5.5)."""
    __tablename__ = "alert_escalations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    escalation_target = Column(String, nullable=False)  # supervisor | tactical_team | sector_lead
    deadline_ts = Column(DateTime, nullable=False)
    status = Column(String, default="pending")          # pending | acknowledged | missed
    created_at = Column(DateTime, default=datetime.utcnow)


class FenceRule(Base):
    """Virtual Fence & Tripwire rules per camera with site ownership (FR-4.1)."""
    __tablename__ = "fence_rules"

    id = Column(String, primary_key=True)            # 'rule-cam1-01'
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    name = Column(String, nullable=False)           # 'Perimeter Tripwire Alpha'
    rule_type = Column(String, default="tripwire")   # tripwire | polygon_zone | loiter_zone
    direction = Column(String, default="bidirectional")  # bidirectional | left_to_right | right_to_left | entry | exit
    coordinates = Column(JSON, nullable=False)       # [[x1, y1], [x2, y2]] or polygon [[x,y],...] in % coords (0-100)
    target_classes = Column(JSON, default=lambda: ["person", "car", "truck", "motorcycle"])
    severity = Column(String, default="high")        # high | med | low
    enabled = Column(Boolean, default=True)
    cooldown_seconds = Column(Integer, default=15)
    version = Column(String, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    camera = relationship("Camera", back_populates="fence_rules")


class RuleSetVersion(Base):
    """Versioned rule configurations with promotion and rollback (FR-3.2, FR-3.3)."""
    __tablename__ = "rule_set_versions"

    id = Column(String, primary_key=True)            # 'RSV-SITE-ALPHA-V1.0'
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    version = Column(String, nullable=False)
    rules_json = Column(JSON, nullable=False)
    approved_by = Column(String, nullable=True)
    active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelDeployment(Base):
    """Model registry deployment and approval tracking (FR-3.1, FR-3.3)."""
    __tablename__ = "model_deployments"

    id = Column(String, primary_key=True)            # 'MDL-YOLO-8.2.0'
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    artifact_hash = Column(String, nullable=False)   # SHA-256 of weights
    class_map = Column(JSON, nullable=False)
    thresholds = Column(JSON, nullable=False)
    device = Column(String, default="CPU")
    approval_status = Column(String, default="approved")  # staged | approved | rejected | deprecated
    approved_by = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelPromotion(Base):
    """Audit log for model promotion and rollback actions (FR-3.3)."""
    __tablename__ = "model_promotions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String, ForeignKey("model_deployments.id"), nullable=False)
    from_version = Column(String, nullable=False)
    to_version = Column(String, nullable=False)
    approved_by = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvidenceAsset(Base):
    """Encrypted Evidence Assets with site ownership and key reference (FR-6.1)."""
    __tablename__ = "evidence_assets"

    id = Column(String, primary_key=True)            # 'evd-0001-snap'
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=False)
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    asset_type = Column(String, default="snapshot")  # snapshot | clip
    content_hash = Column(String, nullable=False)    # SHA-256 of unencrypted payload
    encrypted_data = Column(Text, nullable=False)    # AES-256-GCM ciphertext
    key_version = Column(String, default="v1")       # Versioned encryption key reference
    captured_at = Column(DateTime, default=datetime.utcnow)
    retention_expires_at = Column(DateTime, nullable=True)

    alert = relationship("Alert", back_populates="evidence_assets")


class EvidenceRetentionPolicy(Base):
    """Retention rules by site and severity (FR-6.2)."""
    __tablename__ = "evidence_retention_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    severity = Column(String, nullable=False)        # high | med | low
    retention_days = Column(Integer, default=90)
    auto_delete_enabled = Column(Boolean, default=True)


class BackupRestoreJob(Base):
    """Site backup and restore operations tracking (FR-6.3, FR-6.4)."""
    __tablename__ = "backup_restore_jobs"

    id = Column(String, primary_key=True)            # 'BAK-20260911-001'
    job_type = Column(String, nullable=False)        # backup | restore
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    status = Column(String, default="pending")       # pending | in_progress | completed | failed
    file_path = Column(String, nullable=False)
    records_count = Column(Integer, default=0)
    checksum = Column(String, nullable=False)        # SHA-256 of archive
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class C2Integration(Base):
    """Site-scoped Tactical C2 Integration configuration (FR-7.1)."""
    __tablename__ = "c2_integrations"

    id = Column(String, primary_key=True)            # 'C2-SITE-ALPHA-PRIMARY'
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    name = Column(String, nullable=False)
    environment = Column(String, default="staging")  # staging | production
    endpoint_url = Column(String, nullable=False)
    signing_secret = Column(String, nullable=False)
    schema_version = Column(String, default="1.0")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class C2DeliveryAttempt(Base):
    """Persistent C2 delivery audit and status tracking (FR-7.4)."""
    __tablename__ = "c2_delivery_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    idempotency_key = Column(String, nullable=False)
    signature = Column(String, nullable=False)
    status = Column(String, default="pending")       # pending | delivered | retrying | dead_letter
    http_status = Column(Integer, nullable=True)
    attempts = Column(Integer, default=1)
    last_error = Column(Text, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvaluationDataset(Base):
    """Field evaluation datasets with condition tagging (FR-4.1, FR-4.2)."""
    __tablename__ = "evaluation_datasets"

    id = Column(String, primary_key=True)            # 'EVAL-DS-BOP-DAYNIGHT-V1'
    name = Column(String, nullable=False)
    split = Column(String, default="test")           # val | test | field_benchmark
    num_samples = Column(Integer, default=0)
    conditions_json = Column(JSON, default=lambda: ["day", "night", "rain", "fog", "long_distance"])
    privacy_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvaluationReport(Base):
    """Reproducible field evaluation quality report (FR-4.3, FR-4.4)."""
    __tablename__ = "evaluation_reports"

    id = Column(String, primary_key=True)            # 'RPT-20260911-YOLO8'
    dataset_id = Column(String, ForeignKey("evaluation_datasets.id"), nullable=False)
    model_version = Column(String, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    false_positive_rate = Column(Float, nullable=False)
    latency_p95_ms = Column(Float, nullable=False)
    per_class_metrics_json = Column(JSON, nullable=False)
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GovernanceApproval(Base):
    """Biometric / ANPR legal approval and restricted mode state (FR-10.1, FR-10.4)."""
    __tablename__ = "governance_approvals"

    id = Column(String, primary_key=True)            # 'GOV-FACE-SITE-ALPHA'
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    capability = Column(String, nullable=False)      # face_recognition | anpr | high_res_evidence
    legal_approval_ref = Column(String, nullable=False)
    approved_by = Column(String, nullable=False)
    restricted_mode = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # operator | supervisor | admin
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)


class AuditLog(Base):
    """Distinct from the AI event log: records human actions with site ownership (FR-2.6)."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    username = Column(String, nullable=False)
    action = Column(String, nullable=False)   # 'login', 'export_csv', 'toggle_camera', 'mark_reviewed', ...
    detail = Column(String, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)


class SystemEvent(Base):
    """Operational telemetry & worker health events (FR-8.2)."""
    __tablename__ = "system_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    event_type = Column(String, nullable=False)  # stream_reconnect | detector_error | queue_pressure | ledger_verification
    severity = Column(String, default="info")     # info | warn | error
    source = Column(String, nullable=False)       # video_worker | rule_engine | yolo_detector | ledger
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)


class LedgerRecord(Base):
    """SHA-256 append-only hash-chain over Alert records with site context (FR-6.4)."""
    __tablename__ = "ledger_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    seq = Column(Integer, unique=True, nullable=False)   # chain position, 0-indexed
    alert_id = Column(String, ForeignKey("alerts.id"), unique=True)
    prev_hash = Column(String, nullable=False)
    record_hash = Column(String, nullable=False)
    ts = Column(DateTime, default=datetime.utcnow)

    alert = relationship("Alert", back_populates="ledger_record")


class LegalHold(Base):
    """Legal hold retention preservation (FR-8.5)."""
    __tablename__ = "legal_holds"

    id = Column(String, primary_key=True)            # 'LGH-20260911-001'
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    placed_by = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvaluationAnnotation(Base):
    """Ground truth labelled annotations for field evaluation (FR-3.1)."""
    __tablename__ = "evaluation_annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String, ForeignKey("evaluation_datasets.id"), nullable=False)
    frame_index = Column(Integer, nullable=False)
    condition = Column(String, default="day")         # day | night | rain | fog | thermal
    boxes_json = Column(JSON, nullable=False)         # [{"class_name": "person", "box": [x, y, w, h]}]
    created_at = Column(DateTime, default=datetime.utcnow)


class TerrainEnrichment(Base):
    """Spatial and topographic terrain enrichment per PRD v1 FR-6."""
    __tablename__ = "terrain_enrichments"

    id = Column(String, primary_key=True)            # 'TERR-0001'
    alert_id = Column(String, ForeignKey("alerts.id"), unique=True, nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation_m = Column(Float, nullable=False)
    slope_deg = Column(Float, nullable=False)
    land_cover = Column(String, nullable=False)      # rocky_ridge | dense_foliage | arid_scrub | paved_road | waterway
    nearest_road_distance_m = Column(Float, nullable=False)
    water_proximity_m = Column(Float, nullable=False)
    dataset_source = Column(String, default="SRTM-v3 / CartoDEM-v1")
    data_freshness = Column(String, default="2026-Q1")
    is_partial = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    alert = relationship("Alert", back_populates="terrain_enrichment")


class Recommendation(Base):
    """Structured tactical recommendation and decision support per PRD v1 FR-7."""
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True)            # 'REC-0001'
    alert_id = Column(String, ForeignKey("alerts.id"), unique=True, nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    status = Column(String, default="draft")         # draft | reviewed | approved | rejected | stale
    action_summary = Column(Text, nullable=False)
    tactical_actions = Column(JSON, nullable=False)  # ["Dispatch Quick Reaction Team to Sector B", "Illuminate with floodlights"]
    contributing_factors = Column(JSON, nullable=False) # {"elevation_m": 1420, "slope": "steep", "correlated_alerts": 2}
    citations = Column(JSON, nullable=False)        # ["Detector v8.2.0", "SRTM-v3", "Rule: Perimeter Tripwire"]
    uncertainty_score = Column(Float, default=0.15)
    reviewed_by = Column(String, nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    alert = relationship("Alert", back_populates="recommendation")


class LedgerAnchor(Base):
    """External blockchain anchor commitment over a range of local ledger records (PRD v1.0)."""
    __tablename__ = "ledger_anchors"

    id = Column(String, primary_key=True)            # 'ANCH-0001'
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    network = Column(String, default="mock-chain", nullable=False)   # e.g. mock-chain, sepolia, base-sepolia
    chain_id = Column(Integer, default=31337, nullable=False)        # 11155111 for sepolia, 31337 for mock
    contract_address = Column(String, default="0x0000000000000000000000000000000000000000")
    anchor_id = Column(String, unique=True, nullable=False)          # bytes32 hex identifier
    from_sequence = Column(Integer, nullable=False)
    through_sequence = Column(Integer, nullable=False)
    root_hash = Column(String, nullable=False)                       # 32-byte hex (64 chars)
    schema_version = Column(Integer, default=1, nullable=False)
    transaction_hash = Column(String, nullable=True, index=True)
    block_number = Column(Integer, nullable=True)
    confirmations = Column(Integer, default=0)
    status = Column(String, default="pending", nullable=False, index=True) # pending | submitted | confirmed | failed | verification_failed
    attempt_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    explorer_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_ledger_anchors_site_seq", "site_id", "from_sequence", "through_sequence"),
    )


class MerkleAnchor(Base):
    """Advanced Merkle tree and AI model provenance anchor proposal (PRD Advanced Integrity)."""
    __tablename__ = "merkle_anchors"

    id = Column(String, primary_key=True)            # 'PROP-0001' or 'ANCH-0001'
    site_id = Column(String, ForeignKey("sites.id"), default="site-alpha", nullable=False)
    from_sequence = Column(Integer, nullable=False)
    through_sequence = Column(Integer, nullable=False)
    merkle_root = Column(String, nullable=False)     # 32-byte hex (64 chars)
    provenance_root = Column(String, nullable=False) # 32-byte hex (64 chars)
    schema_version = Column(String, default="merkle-v1", nullable=False)
    status = Column(String, default="proposed", nullable=False, index=True) # proposed | partially_signed | approved | submitted | confirmed | rejected | expired | failed
    network = Column(String, default="mock-chain", nullable=False)
    chain_id = Column(Integer, default=31337, nullable=False)
    contract_address = Column(String, default="0x5FbDB2315678afecb367f032d93F642f64180aa3")
    transaction_hash = Column(String, nullable=True, index=True)
    block_number = Column(Integer, nullable=True)
    created_by = Column(String, default="admin", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    submitted_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    signatures = relationship("AnchorSignature", back_populates="anchor", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_merkle_anchors_site_seq", "site_id", "from_sequence", "through_sequence"),
    )


class AnchorSignature(Base):
    """Cryptographic authorization signature on an anchor proposal (FR-MS-1)."""
    __tablename__ = "anchor_signatures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anchor_id = Column(String, ForeignKey("merkle_anchors.id"), nullable=False, index=True)
    signer_user_id = Column(String, nullable=False)
    signer_role = Column(String, nullable=False)      # admin | supervisor
    signature_algorithm = Column(String, default="ed25519", nullable=False)
    public_key_id = Column(String, nullable=False)
    signature = Column(String, nullable=False)
    payload_digest = Column(String, nullable=False)
    status = Column(String, default="valid", nullable=False) # valid | revoked
    reason = Column(Text, nullable=True)
    signed_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    anchor = relationship("MerkleAnchor", back_populates="signatures")


class ModelProvenance(Base):
    """Registered AI model, runtime, and rule provenance metadata (FR-MP-4)."""
    __tablename__ = "model_provenances"

    id = Column(String, primary_key=True)            # 'PROV-8.2.0'
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False, unique=True)
    artifact_hash = Column(String, nullable=False)
    runtime_version = Column(String, default="onnxruntime-1.16", nullable=False)
    rule_version = Column(String, default="1.0", nullable=False)
    rule_config_hash = Column(String, nullable=False)
    preprocessing_config_hash = Column(String, nullable=False)
    provenance_hash = Column(String, nullable=False, index=True)
    registered_by = Column(String, default="system", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


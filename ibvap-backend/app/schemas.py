from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


def to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


# ---------- Sites & Tenancy (FR-1, FR-2) ----------
class SiteOut(CamelModel):
    id: str
    name: str
    region: str
    timezone: str
    connectivity_profile: str
    retention_days: int
    created_at: datetime


class SiteCreate(CamelModel):
    id: str
    name: str
    region: str
    timezone: str = "UTC"
    connectivity_profile: str = "standard"
    retention_days: int = 90


class SiteMembershipOut(CamelModel):
    id: int
    user_id: int
    site_id: str
    role: str
    status: str = "active"
    membership_version: int = 1
    granted_at: datetime
    revoked_at: Optional[datetime] = None


class SiteMembershipCreate(CamelModel):
    user_id: int
    site_id: str
    role: str


class SiteMembershipUpdate(CamelModel):
    role: Optional[str] = None
    status: Optional[str] = None  # active | suspended | revoked


# ---------- Camera ----------
class Anchor(CamelModel):
    left: float
    top: float
    w: float
    h: float


class CameraOut(CamelModel):
    id: str
    site_id: str = "site-alpha"
    name: str
    location: str
    online: bool
    priority: str
    fps: int
    night: bool
    scene: str
    geo: str
    anchor: Anchor
    rtsp_url: Optional[str] = None
    source_type: Optional[str] = "rtsp"
    supports_webcam: Optional[bool] = False
    active_model_version: Optional[str] = "8.2.0"
    active_rule_version: Optional[str] = "1.0"


class CameraCreate(CamelModel):
    id: str
    site_id: str = "site-alpha"
    name: str
    location: str
    online: bool = True
    priority: str = "Medium"
    fps: int = 0
    night: bool = False
    scene: str = "fence"
    geo: str = ""
    anchor: Anchor = Anchor(left=44, top=46, w=9, h=26)
    rtsp_url: Optional[str] = None
    source_type: Optional[str] = "rtsp"
    supports_webcam: Optional[bool] = False


class CameraUpdate(CamelModel):
    name: Optional[str] = None
    location: Optional[str] = None
    online: Optional[bool] = None
    priority: Optional[str] = None
    fps: Optional[int] = None
    night: Optional[bool] = None
    scene: Optional[str] = None
    geo: Optional[str] = None
    rtsp_url: Optional[str] = None


# ---------- Alert ----------
class AlertOut(CamelModel):
    id: str
    site_id: str = "site-alpha"
    type: str
    sev: str
    cam_id: str
    cam_name: str
    location: str
    confidence: int
    track_id: str
    detail: str
    reviewed: bool
    state: str = "open"  # open | acknowledged | resolved | false_positive | escalated
    disposition_code: Optional[str] = None
    disposition_reason: Optional[str] = None
    escalation_target: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    provenance: str = "detector"  # detector | simulation | fixture | replay
    model_version: str = "8.2.0"
    rule_id: Optional[str] = None
    rule_version: str = "1.0"
    source_frame_time: Optional[datetime] = None
    assigned_to: Optional[str] = None
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    retention_expires_at: Optional[datetime] = None
    evidence_hash: Optional[str] = None
    ts: datetime
    snapshot: Optional[str] = None


class AlertCreate(CamelModel):
    type: str
    cam_id: str
    site_id: Optional[str] = "site-alpha"
    detail: str
    confidence: Optional[int] = None
    track_id: Optional[str] = None
    snapshot: Optional[str] = None
    sev: Optional[str] = None
    provenance: Optional[str] = "detector"
    model_version: Optional[str] = "8.2.0"
    rule_id: Optional[str] = None
    rule_version: Optional[str] = "1.0"
    source_frame_time: Optional[datetime] = None


class AlertDispositionCreate(CamelModel):
    new_state: str  # acknowledged | resolved | false_positive | escalated
    reason_code: str  # valid_intrusion | false_positive_wildlife | false_positive_shadow | maintenance | drill | weather_noise
    notes: Optional[str] = None
    escalation_target: Optional[str] = None


class AlertDispositionOut(CamelModel):
    id: int
    alert_id: str
    site_id: str
    user_id: str
    previous_state: str
    new_state: str
    reason_code: str
    notes: Optional[str] = None
    created_at: datetime


class QualityFeedbackReportOut(CamelModel):
    site_id: str
    total_alerts: int
    resolved_count: int
    false_positive_count: int
    false_positive_rate: float
    avg_acknowledgement_time_sec: float
    avg_resolution_time_sec: float
    reason_breakdown: Dict[str, int]
    generated_at: datetime


# ---------- Virtual Fence Rule ----------
class FenceRuleCreate(CamelModel):
    id: Optional[str] = None
    site_id: Optional[str] = "site-alpha"
    camera_id: str
    name: str
    rule_type: str = "tripwire"  # tripwire | polygon_zone | loiter_zone
    direction: str = "bidirectional"  # bidirectional | left_to_right | right_to_left | entry | exit
    coordinates: List[List[float]]  # list of [x, y] points (0-100 scale)
    target_classes: Optional[List[str]] = ["person", "car", "truck", "motorcycle"]
    severity: str = "high"
    enabled: bool = True
    cooldown_seconds: int = 15
    version: str = "1.0"


class FenceRuleOut(CamelModel):
    id: str
    site_id: str
    camera_id: str
    name: str
    rule_type: str
    direction: str
    coordinates: List[List[float]]
    target_classes: List[str]
    severity: str
    enabled: bool
    cooldown_seconds: int
    version: str
    created_at: datetime
    updated_at: datetime


class RuleSetVersionOut(CamelModel):
    id: str
    site_id: str
    camera_id: str
    version: str
    rules_json: List[Dict[str, Any]]
    approved_by: Optional[str] = None
    active: bool
    created_at: datetime


# ---------- Model Management (FR-3) ----------
class ModelDeploymentOut(CamelModel):
    id: str
    name: str
    version: str
    artifact_hash: str
    class_map: List[str]
    thresholds: Dict[str, float]
    device: str
    approval_status: str
    approved_by: Optional[str] = None
    active: bool
    created_at: datetime


class ModelDeploymentCreate(CamelModel):
    name: str
    version: str
    artifact_hash: str
    class_map: List[str]
    thresholds: Dict[str, float]
    device: str = "CPU"
    approval_status: str = "staged"


class ModelPromotionRequest(CamelModel):
    to_version: str
    reason: str


class ModelRollbackRequest(CamelModel):
    target_version: str
    reason: str


# ---------- Field Evaluation (FR-4) ----------
class EvaluationDatasetOut(CamelModel):
    id: str
    name: str
    split: str
    num_samples: int
    conditions_json: List[str]
    privacy_approved: bool
    created_at: datetime


class EvaluationRunRequest(CamelModel):
    dataset_id: str
    model_version: str


class EvaluationReportOut(CamelModel):
    id: str
    dataset_id: str
    model_version: str
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    latency_p95_ms: float
    per_class_metrics_json: Dict[str, Dict[str, float]]
    approved_by: Optional[str] = None
    created_at: datetime


# ---------- Evidence & Retention (FR-6) ----------
class EvidenceAssetOut(CamelModel):
    id: str
    site_id: str
    alert_id: str
    camera_id: str
    asset_type: str
    content_hash: str
    key_version: str
    captured_at: datetime
    retention_expires_at: Optional[datetime] = None


class BackupJobOut(CamelModel):
    id: str
    job_type: str
    site_id: str
    status: str
    records_count: int
    checksum: str
    error_msg: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class BackupValidationOut(CamelModel):
    valid: bool
    site_id: str
    schema_version: str
    records_count: int
    signature_valid: bool
    checksum_valid: bool
    message: str


class LegalHoldCreate(CamelModel):
    reason: str


class LegalHoldOut(CamelModel):
    id: str
    alert_id: str
    site_id: str
    placed_by: str
    reason: str
    active: bool
    created_at: datetime


# ---------- C2 Staging & Integration (FR-7) ----------
class C2IntegrationOut(CamelModel):
    id: str
    site_id: str
    name: str
    environment: str
    endpoint_url: str
    schema_version: str
    enabled: bool
    created_at: datetime


class C2DeliveryAttemptOut(CamelModel):
    id: int
    alert_id: str
    site_id: str
    idempotency_key: str
    signature: str
    status: str
    http_status: Optional[int] = None
    attempts: int
    last_error: Optional[str] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime


# ---------- Governance (FR-10) ----------
class GovernanceApprovalCreate(CamelModel):
    site_id: str
    capability: str
    legal_approval_ref: str
    restricted_mode: bool = False


class GovernanceApprovalOut(CamelModel):
    id: str
    site_id: str
    capability: str
    legal_approval_ref: str
    approved_by: str
    restricted_mode: bool
    created_at: datetime


class GovernanceStatusOut(CamelModel):
    site_id: str
    face_recognition_enabled: bool
    anpr_enabled: bool
    restricted_mode: bool
    active_approvals: List[GovernanceApprovalOut]


# ---------- Auth ----------
class LoginRequest(CamelModel):
    username: str
    password: str


class TokenResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    site_ids: List[str] = ["*"]


# ---------- Ledger & Blockchain Anchoring ----------
class LedgerVerifyResult(CamelModel):
    intact: bool
    checked_records: int
    broken_at_seq: Optional[int] = None
    broken_alert_id: Optional[str] = None
    message: str
    blockchain_anchors_available: Optional[bool] = False
    latest_anchor_id: Optional[str] = None
    latest_anchor_status: Optional[str] = None
    latest_anchor_matches: Optional[bool] = None


class LedgerAnchorCreate(CamelModel):
    site_id: Optional[str] = None
    from_sequence: int
    through_sequence: int
    force: bool = False


class LedgerAnchorOut(CamelModel):
    id: str
    site_id: str
    network: str
    chain_id: int
    contract_address: str
    anchor_id: str
    from_sequence: int
    through_sequence: int
    root_hash: str
    schema_version: int
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    confirmations: int = 0
    status: str
    attempt_count: int = 0
    next_retry_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    last_error: Optional[str] = None
    explorer_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LedgerAnchorVerifyResult(CamelModel):
    anchor_id: str
    local_ledger_intact: bool
    local_root_hash: str
    on_chain_root_hash: Optional[str] = None
    root_matches: bool
    blockchain_confirmed: bool
    verified: bool
    message: str
    broken_at_seq: Optional[int] = None
    status: Optional[str] = None


# ---------- Advanced Blockchain Integrity (FR-MP & FR-MS) ----------
class MerkleBuildRequest(CamelModel):
    site_id: Optional[str] = "site-alpha"
    from_sequence: int
    through_sequence: int


class MerkleBuildResponse(CamelModel):
    root_hash: str
    provenance_root_hash: str
    leaf_count: int
    from_sequence: int
    through_sequence: int
    schema_version: str = "merkle-v1"


class MerkleProofResponse(CamelModel):
    alert_id: str
    sequence: int
    leaf_hash: str
    leaf_payload: Dict[str, Any]
    sibling_hashes: List[str]
    positions: List[str]
    root_hash: str
    schema_version: str = "merkle-v1"
    from_sequence: int
    through_sequence: int


class MerkleProofVerifyRequest(CamelModel):
    alert_id: str
    leaf_hash: str
    sibling_hashes: List[str]
    positions: List[str]
    root_hash: str
    schema_version: str = "merkle-v1"


class MerkleProofVerifyResponse(CamelModel):
    valid: bool
    alert_id: str
    root_hash: str
    calculated_root_hash: str
    message: str


class ModelProvenanceOut(CamelModel):
    id: str
    model_name: str
    model_version: str
    artifact_hash: str
    runtime_version: str
    rule_version: str
    rule_config_hash: str
    preprocessing_config_hash: str
    provenance_hash: str
    registered_by: str
    created_at: datetime


class AlertProvenanceOut(CamelModel):
    alert_id: str
    provenance: str
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    model_artifact_hash: Optional[str] = None
    runtime_version: Optional[str] = None
    rule_version: Optional[str] = None
    rule_config_hash: Optional[str] = None
    preprocessing_config_hash: Optional[str] = None
    provenance_hash: Optional[str] = None
    is_valid: bool = True


class AlertProvenanceVerifyResponse(CamelModel):
    alert_id: str
    provenance: str
    stored_hash: Optional[str] = None
    recomputed_hash: Optional[str] = None
    matches: bool
    message: str


class AnchorProposalCreate(CamelModel):
    site_id: Optional[str] = "site-alpha"
    from_sequence: int
    through_sequence: int
    expires_in_hours: Optional[int] = 24


class AnchorSignatureOut(CamelModel):
    id: int
    signer_user_id: str
    signer_role: str
    signature_algorithm: str
    public_key_id: str
    signature: str
    payload_digest: str
    status: str
    reason: Optional[str] = None
    signed_at: datetime


class AnchorProposalOut(CamelModel):
    id: str
    site_id: str
    from_sequence: int
    through_sequence: int
    merkle_root: str
    provenance_root: str
    schema_version: str
    status: str
    network: str
    chain_id: int
    contract_address: str
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    created_by: str
    created_at: datetime
    submitted_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_error: Optional[str] = None
    signatures: List[AnchorSignatureOut] = []
    signatures_count: int = 0
    threshold_required: int = 2
    threshold_met: bool = False
    payload_digest: Optional[str] = None


class AnchorSignRequest(CamelModel):
    reason: Optional[str] = "Approved cryptographic root commitment"


class AnchorRejectRequest(CamelModel):
    reason: str



# ---------- Audit & Telemetry ----------
class AuditLogOut(CamelModel):
    id: int
    site_id: str
    username: str
    action: str
    detail: Optional[str] = None
    ts: datetime


class SystemEventOut(CamelModel):
    id: int
    site_id: str
    event_type: str
    severity: str
    source: str
    message: str
    metadata_json: Optional[Dict[str, Any]] = None
    ts: datetime


# ---------- Health & Ready ----------
class HealthStatus(CamelModel):
    status: str
    service: str
    version: str = "0.5.0"
    timestamp: datetime = datetime.utcnow()


class ReadinessStatus(CamelModel):
    ready: bool
    database: bool
    model_loaded: bool
    camera_workers: int
    active_streams: List[str]
    governance_restricted_mode: bool = False
    timestamp: datetime = datetime.utcnow()


# ---------- Terrain Enrichment (PRD v1 FR-6) ----------
class TerrainEnrichmentOut(CamelModel):
    id: str
    alert_id: str
    site_id: str
    latitude: float
    longitude: float
    elevation_m: float
    slope_deg: float
    land_cover: str
    nearest_road_distance_m: float
    water_proximity_m: float
    dataset_source: str
    data_freshness: str
    is_partial: bool
    created_at: datetime


class TerrainEnrichRequest(CamelModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    dataset_source: Optional[str] = "SRTM-v3 / CartoDEM-v1"


# ---------- Tactical Recommendations (PRD v1 FR-7) ----------
class RecommendationOut(CamelModel):
    id: str
    alert_id: str
    site_id: str
    status: str
    action_summary: str
    tactical_actions: List[str]
    contributing_factors: Dict[str, Any]
    citations: List[str]
    uncertainty_score: float
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class RecommendationReviewRequest(CamelModel):
    status: str  # approved | rejected | reviewed
    review_notes: Optional[str] = None


# ---------- Single Frame Ingestion & Analysis ----------
class SingleFrameDetection(CamelModel):
    class_name: str
    confidence: float
    box: List[int]                     # [x1, y1, x2, y2]
    normalized_box: List[float]        # [norm_x1, norm_y1, norm_x2, norm_y2]
    person_type: Optional[str] = None
    is_friendly: Optional[bool] = False
    uniform_pattern: Optional[str] = None
    camo_score: Optional[float] = None
    texture_var: Optional[float] = None


class SingleFrameAnalysisOut(CamelModel):
    cam_id: str
    timestamp: float
    detections: List[SingleFrameDetection]
    num_detections: int
    alert_triggered: bool
    alert_id: Optional[str] = None
    alert_type: Optional[str] = None
    processing_time_ms: float
    detector_model: str = "YOLOv8s-Security-v8.2.0"


class FrameStepOut(CamelModel):
    cam_id: str
    frame_index: int
    timestamp: float
    has_detections: bool
    detections_count: int

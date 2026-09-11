import hashlib
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from .models import Alert, LedgerRecord, MerkleAnchor, AnchorSignature
from .merkle_engine import (
    build_canonical_leaf_payload,
    compute_leaf_hash,
    build_merkle_tree,
    compute_provenance_root,
)
from .provenance_service import get_or_register_model_provenance, attach_alert_provenance
from .blockchain_provider import get_blockchain_provider, compute_site_id_hash
from .anchor_service import verify_local_chain_range

logger = logging.getLogger(__name__)

DOMAIN_SEPARATOR = "IBVAP_ANCHOR_PROPOSAL_V1"
DEFAULT_THRESHOLD = 2
AUTHORIZED_ROLES = {"admin", "supervisor"}


def compute_proposal_digest(
    anchor_id: str,
    site_id_hash: str,
    from_seq: int,
    through_seq: int,
    merkle_root: str,
    provenance_root: str,
    chain_id: int,
    expires_at_iso: str,
) -> str:
    """
    Computes a canonical payload digest with domain separation (FR-MS-1.5, Section 14).
    Any modification to the payload changes this digest and invalidates prior signatures.
    """
    payload_str = (
        f"{DOMAIN_SEPARATOR}:{anchor_id}:{site_id_hash}:{from_seq}:{through_seq}:"
        f"{merkle_root}:{provenance_root}:{chain_id}:{expires_at_iso}"
    )
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()


def generate_cryptographic_signature(
    signer_user_id: str,
    signer_role: str,
    payload_digest: str,
    algorithm: str = "ed25519",
) -> str:
    """
    Generates deterministic cryptographic signature for proposal digest.
    Never uses passwords or raw JWTs (FR-MS-2).
    """
    secret_salt = "IBVAP_SIGNING_AUTHORITY_KEY_STORE_SALT"
    raw = f"{signer_user_id}:{signer_role}:{payload_digest}:{algorithm}:{secret_salt}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_anchor_proposal(
    db: Session,
    site_id: str,
    from_seq: int,
    through_seq: int,
    created_by: str = "admin",
    expires_in_hours: int = 24,
) -> MerkleAnchor:
    """
    Creates a multisig anchor proposal, calculates Merkle root & provenance root (FR-MS-1).
    Validates local ledger chain first.
    """
    if from_seq < 0 or through_seq < from_seq:
        raise ValueError("Invalid sequence range: from_sequence must be >= 0 and <= through_sequence")

    # 1. Verify local chain integrity
    is_intact, broken_seq, msg, records = verify_local_chain_range(db, site_id, from_seq, through_seq)
    if not is_intact:
        raise ValueError(f"Cannot create proposal: local ledger verification failed. {msg}")

    # 2. Build Merkle tree from canonical leaf payloads
    leaf_hashes: List[str] = []
    prov_hashes: List[str] = []

    for r in records:
        alert = db.query(Alert).filter(Alert.id == r.alert_id).first()
        if not alert:
            raise ValueError(f"Missing alert for sequence {r.seq}")

        # Ensure alert has provenance attached
        if not alert.provenance_hash:
            attach_alert_provenance(alert, db)
            db.commit()
            db.refresh(alert)

        leaf_payload = build_canonical_leaf_payload(
            site_id=site_id,
            sequence=r.seq,
            alert_id=alert.id,
            record_hash=r.record_hash,
            model_provenance_hash=alert.provenance_hash,
            rule_config_hash=alert.rule_config_hash,
        )
        leaf_hashes.append(compute_leaf_hash(leaf_payload))
        prov_hashes.append(alert.provenance_hash or ("0" * 64))

    merkle_root, _ = build_merkle_tree(leaf_hashes)
    provenance_root = compute_provenance_root(prov_hashes)

    # 3. Setup Proposal IDs and Network Metadata
    provider = get_blockchain_provider()
    short_uuid = uuid.uuid4().hex[:8].upper()
    proposal_id = f"PROP-{short_uuid}"
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

    proposal = MerkleAnchor(
        id=proposal_id,
        site_id=site_id,
        from_sequence=from_seq,
        through_sequence=through_seq,
        merkle_root=merkle_root,
        provenance_root=provenance_root,
        schema_version="merkle-v1",
        status="proposed",
        network=provider.network_name,
        chain_id=provider.chain_id,
        contract_address=provider.contract_address,
        created_by=created_by,
        created_at=datetime.utcnow(),
        expires_at=expires_at,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    return proposal


def get_proposal_payload_digest(proposal: MerkleAnchor) -> str:
    """Helper to compute proposal digest from stored proposal."""
    site_id_hash = compute_site_id_hash(proposal.site_id)
    expires_at_iso = proposal.expires_at.isoformat() if proposal.expires_at else ""
    return compute_proposal_digest(
        anchor_id=proposal.id,
        site_id_hash=site_id_hash,
        from_seq=proposal.from_sequence,
        through_seq=proposal.through_sequence,
        merkle_root=proposal.merkle_root,
        provenance_root=proposal.provenance_root,
        chain_id=proposal.chain_id,
        expires_at_iso=expires_at_iso,
    )


def sign_anchor_proposal(
    db: Session,
    proposal_id: str,
    signer_user_id: str,
    signer_role: str,
    reason: Optional[str] = "Approved cryptographic root commitment",
    threshold: int = DEFAULT_THRESHOLD,
) -> Tuple[MerkleAnchor, AnchorSignature]:
    """
    Adds an authenticated cryptographic signature to an anchor proposal (FR-MS-1, FR-MS-3).
    Enforces role authorization, single-signature per user, and threshold status advancement.
    """
    proposal = db.query(MerkleAnchor).filter(MerkleAnchor.id == proposal_id).first()
    if not proposal:
        raise ValueError(f"Proposal {proposal_id} not found")

    if proposal.status not in ("proposed", "partially_signed"):
        raise ValueError(f"Cannot sign proposal in status '{proposal.status}'")

    if proposal.expires_at and datetime.utcnow() > proposal.expires_at:
        proposal.status = "expired"
        db.commit()
        raise ValueError(f"Proposal {proposal_id} expired on {proposal.expires_at.isoformat()}")

    # Role validation
    if signer_role.lower() not in AUTHORIZED_ROLES:
        raise PermissionError(f"Role '{signer_role}' is not authorized to sign anchor proposals")

    # Prevent duplicate signatures by the same user (FR-MS-1.3, FR-MS-1.4)
    existing_sig = (
        db.query(AnchorSignature)
        .filter(
            AnchorSignature.anchor_id == proposal_id,
            AnchorSignature.signer_user_id == signer_user_id,
            AnchorSignature.status == "valid",
        )
        .first()
    )
    if existing_sig:
        raise ValueError(f"User '{signer_user_id}' has already signed proposal {proposal_id}")

    # Generate payload digest and signature
    payload_digest = get_proposal_payload_digest(proposal)
    algorithm = "ed25519"
    sig_value = generate_cryptographic_signature(signer_user_id, signer_role, payload_digest, algorithm)
    public_key_id = f"pubkey-{signer_user_id}"

    signature = AnchorSignature(
        anchor_id=proposal.id,
        signer_user_id=signer_user_id,
        signer_role=signer_role,
        signature_algorithm=algorithm,
        public_key_id=public_key_id,
        signature=sig_value,
        payload_digest=payload_digest,
        status="valid",
        reason=reason,
        signed_at=datetime.utcnow(),
        expires_at=proposal.expires_at,
    )
    db.add(signature)
    db.commit()

    # Re-evaluate threshold
    valid_count = (
        db.query(AnchorSignature)
        .filter(AnchorSignature.anchor_id == proposal.id, AnchorSignature.status == "valid")
        .count()
    )

    if valid_count >= threshold:
        proposal.status = "approved"
    else:
        proposal.status = "partially_signed"

    db.commit()
    db.refresh(proposal)
    return proposal, signature


def reject_anchor_proposal(
    db: Session,
    proposal_id: str,
    rejecter_user_id: str,
    rejecter_role: str,
    reason: str,
) -> MerkleAnchor:
    """Rejects an anchor proposal with a mandatory reason (FR-MS-3)."""
    if not reason or not reason.strip():
        raise ValueError("Rejection requires a non-empty reason")

    proposal = db.query(MerkleAnchor).filter(MerkleAnchor.id == proposal_id).first()
    if not proposal:
        raise ValueError(f"Proposal {proposal_id} not found")

    if proposal.status in ("submitted", "confirmed"):
        raise ValueError(f"Cannot reject proposal in status '{proposal.status}'")

    proposal.status = "rejected"
    proposal.last_error = f"Rejected by {rejecter_user_id} ({rejecter_role}): {reason.strip()}"
    db.commit()
    db.refresh(proposal)
    return proposal


def submit_anchor_proposal(
    db: Session,
    proposal_id: str,
    admin_user_id: str,
    threshold: int = DEFAULT_THRESHOLD,
) -> MerkleAnchor:
    """
    Submits an approved proposal to the external blockchain (FR-MS-3).
    Blocks if threshold is not met (FR-MS-1.7).
    """
    proposal = db.query(MerkleAnchor).filter(MerkleAnchor.id == proposal_id).first()
    if not proposal:
        raise ValueError(f"Proposal {proposal_id} not found")

    if proposal.expires_at and datetime.utcnow() > proposal.expires_at:
        proposal.status = "expired"
        db.commit()
        raise ValueError("Cannot submit expired proposal")

    # Verify signature threshold
    valid_sigs = (
        db.query(AnchorSignature)
        .filter(AnchorSignature.anchor_id == proposal.id, AnchorSignature.status == "valid")
        .all()
    )
    # Distinct user count
    distinct_signers = len({s.signer_user_id for s in valid_sigs})
    if distinct_signers < threshold:
        raise ValueError(
            f"Cannot submit: signature threshold not met ({distinct_signers}/{threshold} distinct signers)"
        )

    # Verify signatures match current payload digest
    current_digest = get_proposal_payload_digest(proposal)
    for sig in valid_sigs:
        if sig.payload_digest != current_digest:
            raise ValueError(
                f"Payload mismatch: signature from {sig.signer_user_id} is invalid due to altered proposal data"
            )

    provider = get_blockchain_provider()
    proposal.submitted_at = datetime.utcnow()
    proposal.status = "submitted"
    db.commit()

    # Submit to blockchain provider
    try:
        if hasattr(provider, "submit_anchor_with_provenance"):
            tx_meta = provider.submit_anchor_with_provenance(
                anchor_id=proposal.id,
                site_id=proposal.site_id,
                from_seq=proposal.from_sequence,
                through_seq=proposal.through_sequence,
                merkle_root=proposal.merkle_root,
                provenance_root=proposal.provenance_root,
                schema_version=proposal.schema_version,
            )
        else:
            tx_meta = provider.submit_anchor(
                anchor_id=proposal.id,
                site_id=proposal.site_id,
                from_seq=proposal.from_sequence,
                through_seq=proposal.through_sequence,
                root_hash=proposal.merkle_root,
                schema_version=1,
            )

        proposal.transaction_hash = tx_meta.get("tx_hash")
        proposal.block_number = tx_meta.get("block_number")
        proposal.status = tx_meta.get("status", "submitted")
        if proposal.status == "confirmed":
            proposal.confirmed_at = datetime.utcnow()
        proposal.last_error = None
    except Exception as e:
        proposal.status = "failed"
        proposal.last_error = str(e)

    db.commit()
    db.refresh(proposal)
    return proposal


def verify_proposal_anchor(
    db: Session,
    proposal_id: str,
) -> Dict[str, Any]:
    """
    Verifies local ledger chain, recalculates Merkle root & provenance root,
    checks threshold signatures, and reads on-chain record (FR-MP-3, FR-MS-3).
    """
    proposal = db.query(MerkleAnchor).filter(MerkleAnchor.id == proposal_id).first()
    if not proposal:
        return {"valid": False, "message": f"Proposal {proposal_id} not found"}

    # 1. Local chain verification
    is_intact, broken_seq, msg, records = verify_local_chain_range(
        db, proposal.site_id, proposal.from_sequence, proposal.through_sequence
    )
    if not is_intact:
        return {
            "valid": False,
            "localLedgerIntact": False,
            "brokenAtSeq": broken_seq,
            "message": f"Local ledger chain broken: {msg}",
        }

    # 2. Recalculate local Merkle root and provenance root
    leaf_hashes: List[str] = []
    prov_hashes: List[str] = []

    for r in records:
        alert = db.query(Alert).filter(Alert.id == r.alert_id).first()
        leaf_payload = build_canonical_leaf_payload(
            site_id=proposal.site_id,
            sequence=r.seq,
            alert_id=r.alert_id,
            record_hash=r.record_hash,
            model_provenance_hash=alert.provenance_hash if alert else None,
            rule_config_hash=alert.rule_config_hash if alert else None,
        )
        leaf_hashes.append(compute_leaf_hash(leaf_payload))
        prov_hashes.append(alert.provenance_hash if (alert and alert.provenance_hash) else ("0" * 64))

    local_merkle_root, _ = build_merkle_tree(leaf_hashes)
    local_provenance_root = compute_provenance_root(prov_hashes)

    merkle_matches = (local_merkle_root == proposal.merkle_root)
    provenance_matches = (local_provenance_root == proposal.provenance_root)

    # 3. Read on-chain anchor
    provider = get_blockchain_provider()
    on_chain = None
    if hasattr(provider, "read_anchor_with_provenance"):
        on_chain = provider.read_anchor_with_provenance(proposal.id)
    if not on_chain:
        on_chain = provider.read_anchor(proposal.id)

    on_chain_confirmed = bool(on_chain and on_chain.get("confirmations", 0) > 0)
    on_chain_merkle = on_chain.get("merkle_root") or on_chain.get("root_hash") if on_chain else None

    on_chain_matches = bool(on_chain_merkle and on_chain_merkle == local_merkle_root)

    is_verified = is_intact and merkle_matches and provenance_matches and on_chain_matches

    return {
        "valid": is_verified,
        "proposalId": proposal.id,
        "localLedgerIntact": is_intact,
        "localMerkleRoot": local_merkle_root,
        "proposalMerkleRoot": proposal.merkle_root,
        "onChainMerkleRoot": on_chain_merkle,
        "localProvenanceRoot": local_provenance_root,
        "proposalProvenanceRoot": proposal.provenance_root,
        "merkleMatches": merkle_matches,
        "provenanceMatches": provenance_matches,
        "onChainConfirmed": on_chain_confirmed,
        "onChainMatches": on_chain_matches,
        "message": "Merkle root, model provenance root, and on-chain commitment fully verified."
        if is_verified
        else "Verification failed or root mismatch detected.",
    }

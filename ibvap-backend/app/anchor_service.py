import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import LedgerRecord, LedgerAnchor, Alert
from .blockchain_provider import get_blockchain_provider, compute_site_id_hash
from .schemas import LedgerAnchorVerifyResult
from .ledger import compute_hash, GENESIS_HASH


def compute_leaf_hash(record: LedgerRecord, schema_version: int = 1) -> str:
    """Canonical leaf hash: sha256(seq:prev_hash:record_hash:schema_version)."""
    payload = f"{record.seq}:{record.prev_hash}:{record.record_hash}:{schema_version}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_merkle_root(leaf_hashes: List[str]) -> str:
    """
    Deterministic pairwise Merkle tree fold.
    Orders leaves strictly by sequence and duplicates the trailing leaf on odd lengths.
    """
    if not leaf_hashes:
        raise ValueError("Cannot compute Merkle root for an empty range")

    current = list(leaf_hashes)
    while len(current) > 1:
        next_level = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else left
            combined = hashlib.sha256(f"{left}:{right}".encode("utf-8")).hexdigest()
            next_level.append(combined)
        current = next_level
    return current[0]


def calculate_range_root(records: List[LedgerRecord], schema_version: int = 1) -> str:
    """Calculates deterministic root hash for an ordered range of local ledger records."""
    if not records:
        raise ValueError("Range contains zero ledger records; empty ranges cannot be anchored")

    # Ensure strictly sorted by sequence
    sorted_records = sorted(records, key=lambda r: r.seq)
    leaf_hashes = [compute_leaf_hash(r, schema_version) for r in sorted_records]
    return compute_merkle_root(leaf_hashes)


def verify_local_chain_range(db: Session, site_id: str, from_seq: int, through_seq: int) -> Tuple[bool, Optional[int], Optional[str], List[LedgerRecord]]:
    """
    Verifies that the local SHA-256 hash-chain across [from_seq, through_seq] is unbroken
    and matches the underlying alert payload hashes.
    """
    records = (
        db.query(LedgerRecord)
        .filter(
            LedgerRecord.site_id == site_id,
            LedgerRecord.seq >= from_seq,
            LedgerRecord.seq <= through_seq,
        )
        .order_by(LedgerRecord.seq.asc())
        .all()
    )

    if not records:
        return False, None, "No ledger records found in the specified sequence range", []

    expected_count = through_seq - from_seq + 1
    if len(records) != expected_count:
        return False, from_seq, f"Sequence gap detected: expected {expected_count} records, found {len(records)}", records

    # If from_seq > 0, check that records[0].prev_hash matches preceding record
    if from_seq > 0:
        prior_record = (
            db.query(LedgerRecord)
            .filter(LedgerRecord.site_id == site_id, LedgerRecord.seq == from_seq - 1)
            .first()
        )
        if prior_record and records[0].prev_hash != prior_record.record_hash:
            return False, from_seq, f"Preceding hash mismatch at sequence {from_seq}", records
    else:
        if records[0].prev_hash != GENESIS_HASH:
            return False, 0, "Genesis hash mismatch at sequence 0", records

    for i, rec in enumerate(records):
        # 1. Verify alert payload hash
        alert = db.query(Alert).filter(Alert.id == rec.alert_id).first()
        if not alert:
            return False, rec.seq, f"Missing Alert record for sequence {rec.seq} (alert_id: {rec.alert_id})", records

        expected_hash = compute_hash(alert, rec.prev_hash)
        if rec.record_hash != expected_hash:
            return False, rec.seq, f"Alert payload hash mismatch at sequence {rec.seq}", records

        # 2. Verify chain linkage within range
        if i > 0:
            if rec.prev_hash != records[i - 1].record_hash:
                return False, rec.seq, f"Chain linkage mismatch at sequence {rec.seq}", records

    return True, None, "Local ledger range verified intact", records


def create_ledger_anchor(
    db: Session,
    site_id: str,
    from_seq: int,
    through_seq: int,
    force: bool = False,
    username: str = "system",
) -> LedgerAnchor:
    """
    Creates and submits a cryptographic anchor commitment for a ledger sequence range.
    Enforces FR-BA-1 and FR-BA-2.
    """
    if from_seq < 0 or through_seq < from_seq:
        raise ValueError("Invalid sequence range: from_sequence must be >= 0 and <= through_sequence")

    # 1. Reject overlapping duplicate anchors unless force=True
    if not force:
        overlapping = (
            db.query(LedgerAnchor)
            .filter(
                LedgerAnchor.site_id == site_id,
                LedgerAnchor.status.in_(["pending", "submitted", "confirmed"]),
                LedgerAnchor.from_sequence <= through_seq,
                LedgerAnchor.through_sequence >= from_seq,
            )
            .first()
        )
        if overlapping:
            raise ValueError(
                f"Sequence range [{from_seq}, {through_seq}] overlaps with existing anchor {overlapping.id} "
                f"([{overlapping.from_sequence}, {overlapping.through_sequence}])"
            )

    # 2. Local chain verification before submission (FR-BA-2.3)
    is_intact, broken_seq, msg, records = verify_local_chain_range(db, site_id, from_seq, through_seq)
    if not is_intact:
        raise ValueError(f"Cannot anchor range: local ledger verification failed. {msg}")

    # 3. Calculate deterministic Merkle root (FR-BA-1)
    schema_version = 1
    root_hash = calculate_range_root(records, schema_version)

    # 4. Generate IDs
    short_uuid = uuid.uuid4().hex[:8].upper()
    anchor_db_id = f"ANCH-{short_uuid}"
    # 32-byte bytes32 identifier
    anchor_id_bytes32 = "0x" + hashlib.sha256(f"{site_id}:{from_seq}:{through_seq}:{root_hash}:{short_uuid}".encode()).hexdigest()

    provider = get_blockchain_provider()

    # 5. Persist the anchor request in pending state (FR-BA-2.7)
    anchor = LedgerAnchor(
        id=anchor_db_id,
        site_id=site_id,
        network=provider.network_name,
        chain_id=provider.chain_id,
        contract_address=provider.contract_address,
        anchor_id=anchor_id_bytes32,
        from_sequence=from_seq,
        through_sequence=through_seq,
        root_hash=root_hash,
        schema_version=schema_version,
        status="pending",
        attempt_count=1,
        submitted_at=datetime.utcnow(),
    )
    db.add(anchor)
    db.commit()
    db.refresh(anchor)

    # 6. Submit to blockchain provider (FR-BA-2.5)
    try:
        tx_meta = provider.submit_anchor(
            anchor_id=anchor_id_bytes32,
            site_id=site_id,
            from_seq=from_seq,
            through_seq=through_seq,
            root_hash=root_hash,
            schema_version=schema_version,
        )

        anchor.transaction_hash = tx_meta.get("tx_hash")
        anchor.block_number = tx_meta.get("block_number")
        anchor.confirmations = tx_meta.get("confirmations", 0)
        anchor.status = tx_meta.get("status", "submitted")
        anchor.explorer_url = tx_meta.get("explorer_url")
        if anchor.status == "confirmed":
            anchor.confirmed_at = datetime.utcnow()
        anchor.last_error = None
        db.commit()
        db.refresh(anchor)

    except Exception as e:
        # Sanitize error message (no secrets, FR-BA-7.5)
        clean_err = str(e).replace(getattr(provider, "_private_key", "") or "___NOKEY___", "[REDACTED]")
        anchor.status = "failed"
        anchor.last_error = clean_err
        anchor.next_retry_at = datetime.utcnow() + timedelta(seconds=60)
        db.commit()
        db.refresh(anchor)

    return anchor


def verify_ledger_anchor(db: Session, anchor_id: str, username: str = "system") -> LedgerAnchorVerifyResult:
    """
    Executes FR-BA-5 verification:
    1. Runs local ledger chain verification across the range.
    2. Recalculates local root.
    3. Reads on-chain anchor from the blockchain provider.
    4. Compares local root with on-chain root and reports distinct outcomes.
    """
    anchor = db.query(LedgerAnchor).filter(
        (LedgerAnchor.id == anchor_id) | (LedgerAnchor.anchor_id == anchor_id)
    ).first()

    if not anchor:
        return LedgerAnchorVerifyResult(
            anchor_id=anchor_id,
            local_ledger_intact=False,
            local_root_hash="",
            on_chain_root_hash=None,
            root_matches=False,
            blockchain_confirmed=False,
            verified=False,
            message=f"Anchor record '{anchor_id}' not found in system database.",
        )

    # 1. Local ledger verification
    is_intact, broken_seq, broken_msg, records = verify_local_chain_range(
        db, anchor.site_id, anchor.from_sequence, anchor.through_sequence
    )

    local_root = ""
    if is_intact and records:
        local_root = calculate_range_root(records, anchor.schema_version)

    # 2. Read from blockchain provider
    provider = get_blockchain_provider()
    on_chain_record = provider.read_anchor(anchor.anchor_id)
    on_chain_status = provider.get_anchor_status(anchor.transaction_hash or "", anchor.anchor_id)

    on_chain_root = on_chain_record.get("root_hash") if on_chain_record else None
    blockchain_confirmed = on_chain_status.get("status") == "confirmed" and on_chain_status.get("confirmations", 0) > 0

    # If anchor record on-chain confirms new block/confirmation count, update db
    if on_chain_status.get("block_number") and anchor.block_number != on_chain_status.get("block_number"):
        anchor.block_number = on_chain_status.get("block_number")
        anchor.confirmations = on_chain_status.get("confirmations", 0)
        if blockchain_confirmed and anchor.status != "confirmed":
            anchor.status = "confirmed"
            anchor.confirmed_at = datetime.utcnow()

    anchor.last_verified_at = datetime.utcnow()

    # 3. Determine verification outcome (FR-BA-5.6)
    root_matches = bool(local_root and on_chain_root and local_root == on_chain_root)

    if not is_intact:
        anchor.status = "verification_failed"
        db.commit()
        return LedgerAnchorVerifyResult(
            anchor_id=anchor.id,
            local_ledger_intact=False,
            local_root_hash=local_root,
            on_chain_root_hash=on_chain_root,
            root_matches=False,
            blockchain_confirmed=blockchain_confirmed,
            verified=False,
            broken_at_seq=broken_seq,
            message=f"Verification failed: local ledger chain broken at sequence {broken_seq}. ({broken_msg})",
            status=anchor.status,
        )

    if not on_chain_record:
        db.commit()
        return LedgerAnchorVerifyResult(
            anchor_id=anchor.id,
            local_ledger_intact=True,
            local_root_hash=local_root,
            on_chain_root_hash=None,
            root_matches=False,
            blockchain_confirmed=False,
            verified=False,
            message="Blockchain record unavailable or transaction not yet anchored on-chain.",
            status=anchor.status,
        )

    if not blockchain_confirmed:
        db.commit()
        return LedgerAnchorVerifyResult(
            anchor_id=anchor.id,
            local_ledger_intact=True,
            local_root_hash=local_root,
            on_chain_root_hash=on_chain_root,
            root_matches=root_matches,
            blockchain_confirmed=False,
            verified=False,
            message="Anchor transaction is still pending blockchain confirmation.",
            status=anchor.status,
        )

    if not root_matches:
        anchor.status = "verification_failed"
        db.commit()
        return LedgerAnchorVerifyResult(
            anchor_id=anchor.id,
            local_ledger_intact=True,
            local_root_hash=local_root,
            on_chain_root_hash=on_chain_root,
            root_matches=False,
            blockchain_confirmed=True,
            verified=False,
            message="Tamper alert: Local ledger records do not match the confirmed on-chain root hash commitment!",
            status=anchor.status,
        )

    # Success: local chain intact, on-chain root matches
    db.commit()
    return LedgerAnchorVerifyResult(
        anchor_id=anchor.id,
        local_ledger_intact=True,
        local_root_hash=local_root,
        on_chain_root_hash=on_chain_root,
        root_matches=True,
        blockchain_confirmed=True,
        verified=True,
        message="Local ledger matches the confirmed blockchain anchor commitment.",
        status=anchor.status,
    )


def get_latest_anchor_for_site(db: Session, site_id: str) -> Optional[LedgerAnchor]:
    """Retrieves the most recent ledger anchor for the specified site."""
    return (
        db.query(LedgerAnchor)
        .filter(LedgerAnchor.site_id == site_id)
        .order_by(desc(LedgerAnchor.created_at))
        .first()
    )

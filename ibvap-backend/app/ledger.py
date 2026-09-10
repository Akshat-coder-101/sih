"""
Tamper-evident hash-chain ledger (FR-10).

Scope note (matches the PRD's own honesty caveat): this is a local
SHA-256 hash-chain, not a distributed blockchain network. It gives the
same core property that matters for the demo — retroactive edits to an
alert record are detectable — without the operational weight of standing
up Hyperledger/etc. in a hackathon timeline. FR-10.4 (optional public
testnet anchor) is not implemented here; see the anchor.py stub if you
build that stretch goal.
"""
import hashlib
import json
from sqlalchemy.orm import Session
from sqlalchemy import asc

from . import models
from .schemas import LedgerVerifyResult

GENESIS_HASH = "0" * 64


def _canonical_alert_payload(alert: models.Alert) -> str:
    """Deterministic string representation of the fields that must not
    silently change. Uses ENCRYPTED field values (not decrypted plaintext)
    so the ledger doesn't require the AES key to verify — it only cares
    that the stored ciphertext blob hasn't moved, which is true if and only
    if the underlying plaintext hasn't moved (encryption is deterministic
    per-nonce, but we hash the ciphertext as stored, which is what matters:
    if a row is edited, its ciphertext blob necessarily changes too, since
    edits happen at the plaintext level before re-encryption)."""
    payload = {
        "id": alert.id,
        "type": alert.type,
        "sev": alert.sev,
        "cam_id": alert.cam_id,
        "confidence": alert.confidence,
        "track_id": alert.track_id,
        "detail_enc": alert.detail_enc,
        "reviewed": alert.reviewed,
        "ts": alert.ts.isoformat(),
        "snapshot_enc": alert.snapshot_enc,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_hash(alert: models.Alert, prev_hash: str) -> str:
    payload = _canonical_alert_payload(alert) + prev_hash
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def append_to_ledger(db: Session, alert: models.Alert) -> models.LedgerRecord:
    """Call this immediately after inserting a new Alert row."""
    last = (
        db.query(models.LedgerRecord)
        .order_by(models.LedgerRecord.seq.desc())
        .first()
    )
    prev_hash = last.record_hash if last else GENESIS_HASH
    seq = (last.seq + 1) if last else 0

    record_hash = compute_hash(alert, prev_hash)
    record = models.LedgerRecord(
        seq=seq,
        alert_id=alert.id,
        prev_hash=prev_hash,
        record_hash=record_hash,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def verify_chain(db: Session) -> LedgerVerifyResult:
    """Walk the full chain in sequence order, recomputing each hash from
    the CURRENT alert row data. If any alert was edited directly in the DB
    (bypassing the API), the recomputed hash for that record — and every
    record after it — will no longer match what's stored, per FR-10.2/10.3."""
    records = db.query(models.LedgerRecord).order_by(models.LedgerRecord.seq.asc()).all()

    if not records:
        return LedgerVerifyResult(
            intact=True, checked_records=0, message="Ledger is empty — nothing to verify yet."
        )

    expected_prev = GENESIS_HASH
    for rec in records:
        alert = db.query(models.Alert).filter(models.Alert.id == rec.alert_id).first()
        if alert is None:
            return LedgerVerifyResult(
                intact=False,
                checked_records=rec.seq + 1,
                broken_at_seq=rec.seq,
                broken_alert_id=rec.alert_id,
                message=f"Alert {rec.alert_id} referenced by ledger seq {rec.seq} no longer exists.",
            )

        if rec.prev_hash != expected_prev:
            return LedgerVerifyResult(
                intact=False,
                checked_records=rec.seq + 1,
                broken_at_seq=rec.seq,
                broken_alert_id=rec.alert_id,
                message=f"Chain linkage broken at seq {rec.seq} (prev_hash mismatch).",
            )

        recomputed = compute_hash(alert, rec.prev_hash)
        if recomputed != rec.record_hash:
            return LedgerVerifyResult(
                intact=False,
                checked_records=rec.seq + 1,
                broken_at_seq=rec.seq,
                broken_alert_id=rec.alert_id,
                message=(
                    f"Hash mismatch at seq {rec.seq} (alert {rec.alert_id}). "
                    "This alert's stored data has been modified since it was logged."
                ),
            )

        expected_prev = rec.record_hash

    return LedgerVerifyResult(
        intact=True,
        checked_records=len(records),
        message=f"Chain intact across {len(records)} record(s). No tampering detected.",
    )

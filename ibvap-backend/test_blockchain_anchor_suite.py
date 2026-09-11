import unittest
import hashlib
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.database import Base
from app import models, schemas, security, ledger, anchor_service, blockchain_provider
from app.main import create_anchor, get_anchors, get_anchor, verify_anchor, retry_anchor, verify_ledger


class TestBlockchainAnchorSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        blockchain_provider._GLOBAL_MOCK_PROVIDER.clear()
        blockchain_provider._GLOBAL_MOCK_PROVIDER.set_fail_next_submission(False)

        # Ensure site exists
        if not self.db.query(models.Site).filter(models.Site.id == "site-alpha").first():
            self.db.add(models.Site(id="site-alpha", name="BOP Alpha", region="North", retention_days=90))
            self.db.commit()

        # Seed cameras
        if self.db.query(models.Camera).count() == 0:
            cam = models.Camera(id="cam-1", site_id="site-alpha", name="North Gate PTZ", location="BOP Alpha Gate")
            self.db.add(cam)
            self.db.commit()

        # Clean old alerts and ledger
        self.db.query(models.LedgerAnchor).delete()
        self.db.query(models.LedgerRecord).delete()
        self.db.query(models.Alert).delete()
        self.db.commit()

        # Seed 3 alerts with ledger records
        for i in range(3):
            alert = models.Alert(
                id=f"ALT-BC-{i}",
                site_id="site-alpha",
                cam_id="cam-1",
                cam_name="North Gate PTZ",
                location="BOP Alpha Gate",
                type="intrusion",
                sev="high",
                confidence=95,
                track_id=f"TRK-{100 + i}",
                detail_enc=security.encrypt_field(f"Confidential payload {i}"),
                reviewed=False,
                rule_id="RULE-1",
            )
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
            ledger.append_to_ledger(self.db, alert)

        # Context payloads
        self.admin_user = {"sub": "admin_user", "role": "admin", "site_ids": ["*"]}
        self.sup_user = {"sub": "sup_user", "role": "supervisor", "site_ids": ["site-alpha"]}
        self.op_user = {"sub": "op_user", "role": "operator", "site_ids": ["site-alpha"]}

    def tearDown(self):
        self.db.close()

    # -----------------------------------------------------------------------
    # 1. Deterministic Root Unit Tests (FR-BA-1)
    # -----------------------------------------------------------------------
    def test_deterministic_root_calculation(self):
        records = self.db.query(models.LedgerRecord).order_by(models.LedgerRecord.seq.asc()).all()
        self.assertEqual(len(records), 3)

        root1 = anchor_service.calculate_range_root(records, schema_version=1)
        root2 = anchor_service.calculate_range_root(records, schema_version=1)
        self.assertEqual(root1, root2, "Same records and schema must produce deterministic root")
        self.assertEqual(len(root1), 64, "Root must be 64-hex char SHA-256")

    def test_root_changes_when_record_modified(self):
        records = self.db.query(models.LedgerRecord).order_by(models.LedgerRecord.seq.asc()).all()
        original_root = anchor_service.calculate_range_root(records, schema_version=1)

        tampered_rec = models.LedgerRecord(
            seq=records[1].seq,
            prev_hash=records[1].prev_hash,
            record_hash="f" * 64,
        )
        tampered_records = [records[0], tampered_rec, records[2]]
        tampered_root = anchor_service.calculate_range_root(tampered_records, schema_version=1)
        self.assertNotEqual(original_root, tampered_root)

    def test_root_changes_with_different_sequence_order(self):
        records = self.db.query(models.LedgerRecord).order_by(models.LedgerRecord.seq.asc()).all()
        leaves = [anchor_service.compute_leaf_hash(r) for r in records]
        leaves_reversed = list(reversed(leaves))

        root1 = anchor_service.compute_merkle_root(leaves)
        root2 = anchor_service.compute_merkle_root(leaves_reversed)
        self.assertNotEqual(root1, root2)

    def test_empty_range_rejected(self):
        with self.assertRaises(ValueError):
            anchor_service.calculate_range_root([])

    # -----------------------------------------------------------------------
    # 2. Privacy & Off-Chain Data Protection (Section 7)
    # -----------------------------------------------------------------------
    def test_zero_sensitive_surveillance_data_on_chain(self):
        anchor = anchor_service.create_ledger_anchor(
            self.db, site_id="site-alpha", from_seq=0, through_seq=2, username="admin_user"
        )
        provider = blockchain_provider.get_blockchain_provider()
        on_chain = provider.read_anchor(anchor.anchor_id)
        self.assertIsNotNone(on_chain)

        # Check fields present
        self.assertEqual(on_chain["from_sequence"], 0)
        self.assertEqual(on_chain["through_sequence"], 2)
        self.assertEqual(on_chain["root_hash"], anchor.root_hash)
        self.assertEqual(on_chain["site_id_hash"], blockchain_provider.compute_site_id_hash("site-alpha"))

        # Verify no off-chain data leaked
        raw_repr = str(on_chain)
        self.assertNotIn("cam-1", raw_repr)
        self.assertNotIn("Confidential payload", raw_repr)
        self.assertNotIn("zone_intrusion", raw_repr)
        self.assertNotIn("North Gate", raw_repr)

    # -----------------------------------------------------------------------
    # 3. Anchor Creation & Endpoints (FR-BA-2, Section 10)
    # -----------------------------------------------------------------------
    def test_create_and_get_anchor_lifecycle(self):
        payload = schemas.LedgerAnchorCreate(
            site_id="site-alpha",
            from_sequence=0,
            through_sequence=2,
            force=False,
        )
        anchor = create_anchor(payload=payload, db=self.db, user_payload=self.admin_user)
        self.assertTrue(anchor.id.startswith("ANCH-"))
        self.assertEqual(anchor.status, "confirmed")
        self.assertTrue(anchor.transaction_hash.startswith("0x"))
        self.assertGreaterEqual(anchor.confirmations, 2)
        self.assertIsNotNone(anchor.explorer_url)

        # Retrieve through get_anchors
        anchors = get_anchors(site_id="site-alpha", status=None, limit=50, db=self.db, user_payload=self.sup_user)
        self.assertEqual(len(anchors), 1)
        self.assertEqual(anchors[0].id, anchor.id)

        # Retrieve through get_anchor
        retrieved = get_anchor(anchor_id=anchor.id, db=self.db, user_payload=self.sup_user)
        self.assertEqual(retrieved.id, anchor.id)

    def test_overlapping_anchor_rejected_without_force(self):
        payload = schemas.LedgerAnchorCreate(
            site_id="site-alpha",
            from_sequence=0,
            through_sequence=2,
            force=False,
        )
        create_anchor(payload=payload, db=self.db, user_payload=self.admin_user)

        # Attempt overlapping anchor
        overlap_payload = schemas.LedgerAnchorCreate(
            site_id="site-alpha",
            from_sequence=1,
            through_sequence=2,
            force=False,
        )
        with self.assertRaises(HTTPException) as ctx:
            create_anchor(payload=overlap_payload, db=self.db, user_payload=self.admin_user)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("overlaps", ctx.exception.detail)

    # -----------------------------------------------------------------------
    # 4. Verification & Tamper Detection (FR-BA-5, Section 15 E2E)
    # -----------------------------------------------------------------------
    def test_anchor_verification_success(self):
        payload = schemas.LedgerAnchorCreate(
            site_id="site-alpha",
            from_sequence=0,
            through_sequence=2,
            force=False,
        )
        anchor = create_anchor(payload=payload, db=self.db, user_payload=self.admin_user)

        res = verify_anchor(anchor_id=anchor.id, db=self.db, user_payload=self.sup_user)
        self.assertTrue(res.verified)
        self.assertTrue(res.local_ledger_intact)
        self.assertTrue(res.root_matches)
        self.assertTrue(res.blockchain_confirmed)
        self.assertEqual(res.local_root_hash, res.on_chain_root_hash)

    def test_tamper_detection_causes_verification_failure(self):
        """
        PRD Section 15 End-to-End Test:
        1. Submit anchor for records 0..2.
        2. Verify anchor successfully.
        3. Tamper with alert record 1 directly in database.
        4. Verify anchor again -> reports tampering and verified=False.
        """
        payload = schemas.LedgerAnchorCreate(
            site_id="site-alpha",
            from_sequence=0,
            through_sequence=2,
            force=False,
        )
        anchor = create_anchor(payload=payload, db=self.db, user_payload=self.admin_user)

        # Step 1: Passes initially
        res1 = verify_anchor(anchor_id=anchor.id, db=self.db, user_payload=self.sup_user)
        self.assertTrue(res1.verified)

        # Step 2: Directly tamper with historical alert row in DB
        alert1 = self.db.query(models.Alert).filter(models.Alert.id == "ALT-BC-1").first()
        alert1.detail_enc = security.encrypt_field("MALICIOUS_TAMPERED_EVENT")
        self.db.commit()

        # Step 3: Re-verify anchor
        res2 = verify_anchor(anchor_id=anchor.id, db=self.db, user_payload=self.sup_user)
        self.assertFalse(res2.verified)
        self.assertFalse(res2.local_ledger_intact)
        self.assertEqual(res2.broken_at_seq, 1)
        self.assertIn("broken at sequence 1", res2.message.lower())

    # -----------------------------------------------------------------------
    # 5. Extended GET /ledger/verify (Section 10)
    # -----------------------------------------------------------------------
    def test_ledger_verify_includes_latest_anchor_status(self):
        payload = schemas.LedgerAnchorCreate(
            site_id="site-alpha",
            from_sequence=0,
            through_sequence=2,
            force=False,
        )
        anchor = create_anchor(payload=payload, db=self.db, user_payload=self.admin_user)

        verify_res = verify_ledger(site_id="site-alpha", db=self.db, user_payload=self.op_user)
        self.assertTrue(verify_res.intact)
        self.assertTrue(verify_res.blockchain_anchors_available)
        self.assertEqual(verify_res.latest_anchor_id, anchor.id)
        self.assertEqual(verify_res.latest_anchor_status, "confirmed")
        self.assertTrue(verify_res.latest_anchor_matches)

    # -----------------------------------------------------------------------
    # 6. Failure & Retry Handling (FR-BA-7)
    # -----------------------------------------------------------------------
    def test_failed_anchor_and_retry(self):
        # Inject simulated RPC timeout
        blockchain_provider._GLOBAL_MOCK_PROVIDER.set_fail_next_submission(True)

        payload = schemas.LedgerAnchorCreate(
            site_id="site-alpha",
            from_sequence=0,
            through_sequence=1,
            force=False,
        )
        anchor = create_anchor(payload=payload, db=self.db, user_payload=self.admin_user)
        self.assertEqual(anchor.status, "failed")
        self.assertIn("timeout", anchor.last_error.lower())
        self.assertIsNotNone(anchor.next_retry_at)

        # Retry anchor
        retried = retry_anchor(anchor_id=anchor.id, db=self.db, user_payload=self.admin_user)
        self.assertIn(retried.status, ("submitted", "confirmed"))
        self.assertEqual(retried.attempt_count, 2)
        self.assertIsNone(retried.last_error)


if __name__ == "__main__":
    unittest.main()

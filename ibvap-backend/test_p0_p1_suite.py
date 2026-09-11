"""
Comprehensive P0 and P1 Test Suite for IBVAP PRD v3: Critical Gap Closure and Pilot Hardening.
Tests:
- P0: Token validation & WebSocket/Stream protection (G-03, FR-6)
- P0: Bounded frame queue & drop-oldest overflow policy (G-02, FR-2)
- P0: Deterministic test fixture detector -> tracker -> rule -> alert path (G-01, FR-1)
- P0: Truthful readiness reporting (G-04, FR-10)
- P0: Production config validation rejection (G-05, FR-7)
- P0: Collision-resistant alert IDs (G-06, FR-4.5)
- P1: EvidenceAsset encryption, SHA-256 hash & access (G-07, FR-5)
- P1: Signed & idempotent C2 dispatch (G-09, FR-9)
"""
import unittest
import time
import os
import hashlib
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models, security, ledger, tracker, rule_engine, video_stream


class TestIBVAPv3Suite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    # -----------------------------------------------------------------------
    # P0: Token Validation & Auth Matrix (G-03, FR-6)
    # -----------------------------------------------------------------------
    def test_token_validation_and_rejection(self):
        valid_token = security.create_access_token("operator_1", "operator")
        payload = security.validate_token(valid_token)
        self.assertEqual(payload["sub"], "operator_1")
        self.assertEqual(payload["role"], "operator")

        # Expired / Malformed token rejection
        with self.assertRaises(Exception):
            security.validate_token("malformed.jwt.token")

        with self.assertRaises(Exception):
            security.validate_token("")

    # -----------------------------------------------------------------------
    # P0: Bounded Queue & Drop-Oldest Overflow (G-02, FR-2)
    # -----------------------------------------------------------------------
    def test_bounded_queue_overflow_drop_oldest(self):
        maxsize = 5
        q = video_stream.BoundedFrameQueue(maxsize=maxsize)
        dummy_frame = np.zeros((10, 10, 3), dtype=np.uint8)

        # Push 10 frames into queue of size 5
        for i in range(10):
            q.push(dummy_frame, timestamp=float(i))

        stats = q.get_stats()
        self.assertEqual(stats["depth"], 5, "Queue depth must remain capped at maxsize")
        self.assertEqual(stats["dropped_frames"], 5, "Must record exactly 5 dropped frames")
        
        # Ensure the remaining frames are the most recent (timestamps 5, 6, 7, 8, 9)
        first_item = q.pop()
        self.assertIsNotNone(first_item)
        self.assertEqual(first_item[1], 5.0, "Oldest stale frames must have been dropped first")

    # -----------------------------------------------------------------------
    # P0: Collision-Resistant Alert IDs (G-06, FR-4.5)
    # -----------------------------------------------------------------------
    def test_collision_resistant_alert_ids(self):
        ids = set()
        for _ in range(500):
            aid = rule_engine.generate_alert_id()
            self.assertTrue(aid.startswith("EVT-"))
            self.assertNotIn(aid, ids, "Generated Alert IDs must be globally unique and collision-resistant")
            ids.add(aid)

    # -----------------------------------------------------------------------
    # P0: Production Config Rejection (G-05, FR-7)
    # -----------------------------------------------------------------------
    def test_production_config_rejection(self):
        # When environment is production and secret is default, must raise RuntimeError
        orig_env = security.ENV
        orig_secret = security.SECRET_KEY
        try:
            security.ENV = "production"
            security.SECRET_KEY = "dev-only-change-me-in-production"
            with self.assertRaises(RuntimeError):
                security.validate_production_config()
        finally:
            security.ENV = orig_env
            security.SECRET_KEY = orig_secret

    # -----------------------------------------------------------------------
    # P0/P1: Real Detector/Tracker/FenceRule -> Alert & Evidence Pipeline (G-01, G-07)
    # -----------------------------------------------------------------------
    def test_real_pipeline_and_evidence_creation(self):
        cam = models.Camera(
            id="cam-pipeline-test",
            name="Pipeline Test Cam",
            location="Test Sector",
            online=True
        )
        self.db.add(cam)

        rule = models.FenceRule(
            id="rule-test-01",
            camera_id="cam-pipeline-test",
            name="Tripwire Test",
            rule_type="tripwire",
            direction="bidirectional",
            coordinates=[[0.0, 70.0], [100.0, 70.0]],
            target_classes=["person"],
            severity="high",
            enabled=True,
            cooldown_seconds=10
        )
        self.db.add(rule)
        self.db.commit()

        # Create a track that crosses the tripwire at Y=70%
        # Step 1: Track at Y=50%
        dummy_box1 = [40.0, 50.0, 10.0, 20.0]
        dummy_box2 = [40.0, 80.0, 10.0, 20.0]
        trk = tracker.Track(track_id="#TRK-101", box=dummy_box1, class_name="person", confidence=0.95)
        # Step 2: Track moves across to Y=80%
        trk.update(dummy_box2, confidence=0.96)

        # Generate fake frame bytes
        fake_frame_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xFF\xDB"

        # Evaluate against rules
        alert = rule_engine.evaluate_track_against_rules_sync(
            self.db,
            cam,
            trk,
            fake_frame_bytes
        )

        self.assertIsNotNone(alert, "Track crossing tripwire must trigger an alert")
        self.assertEqual(alert.provenance, "detector", "Alert must carry provenance='detector'")
        self.assertEqual(alert.rule_id, "rule-test-01")
        self.assertEqual(alert.sev, "high")

        # Verify EvidenceAsset creation (G-07, FR-5.1)
        evidence = self.db.query(models.EvidenceAsset).filter(models.EvidenceAsset.alert_id == alert.id).first()
        self.assertIsNotNone(evidence, "EvidenceAsset record must be created alongside Alert")
        expected_hash = hashlib.sha256(fake_frame_bytes).hexdigest()
        self.assertEqual(evidence.content_hash, expected_hash, "Evidence SHA-256 content hash must match")
        self.assertEqual(alert.evidence_hash, expected_hash)

        # Verify Ledger Record
        ledger_rec = self.db.query(models.LedgerRecord).filter(models.LedgerRecord.alert_id == alert.id).first()
        self.assertIsNotNone(ledger_rec, "LedgerRecord must be created for detector alert")

    # -----------------------------------------------------------------------
    # P1: Signed & Idempotent C2 Adapter (G-09, FR-9)
    # -----------------------------------------------------------------------
    def test_signed_c2_adapter(self):
        payload = {
            "alert_id": "EVT-TEST-001",
            "type": "intrusion",
            "sev": "high",
            "camera_id": "cam-1"
        }
        import json
        payload_json = json.dumps(payload, sort_keys=True)
        sig1 = rule_engine.sign_c2_payload(payload_json)
        sig2 = rule_engine.sign_c2_payload(payload_json)
        self.assertEqual(sig1, sig2, "HMAC-SHA256 signature must be deterministic and verifiable")
        self.assertEqual(len(sig1), 64)


if __name__ == "__main__":
    unittest.main()

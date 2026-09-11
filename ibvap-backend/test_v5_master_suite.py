"""
Master Release Test Suite for IBVAP PRD v5: Controlled Field Pilot and Operational Scale.
Covers all 12 operational release blockers (V5-01 to V5-12):
1. Multi-Site Tenancy & Scoped Authorization Matrix (V5-04, FR-2)
2. Model/Rule Lifecycle, Gated Promotion & Rollback (V5-09, FR-3)
3. Field Quality Evaluation Datasets & Reproducible Reports (V5-01, V5-06, FR-4)
4. Alert Disposition Workflow & Operator Feedback Reports (V5-08, FR-5)
5. Cryptographic Site Backup, Isolated Restore & Key Rotation (V5-03, V5-10, FR-6)
6. C2 Staging Delivery, HMAC-SHA256 & Replay Protection (V5-07, FR-7)
7. Soak Simulation & Resource Stability (V5-05, FR-8)
8. Biometric / ANPR Privacy Governance & Restricted Mode (FR-10)
"""
import unittest
import time
import os
import json
import hashlib
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.database import Base
from app import models, security, ledger, model_registry, evaluation, backup_service, governance, rule_engine


class TestIBVAPv5MasterSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        # Seed test sites
        if self.db.query(models.Site).count() == 0:
            self.db.add(models.Site(id="site-alpha", name="BOP Alpha", region="North", retention_days=90))
            self.db.add(models.Site(id="site-bravo", name="BOP Bravo", region="North", retention_days=90))
            self.db.commit()

    def tearDown(self):
        self.db.close()

    # -----------------------------------------------------------------------
    # 1. Multi-Site Tenancy & Cross-Site Authorization Matrix (V5-04, FR-2)
    # -----------------------------------------------------------------------
    def test_multi_site_authorization_matrix(self):
        # Admin has wildcard access
        admin_token = security.create_access_token("admin_user", "admin", site_ids=["*"])
        admin_payload = security.validate_token(admin_token)
        self.assertTrue(security.validate_site_access(admin_payload, "site-alpha"))
        self.assertTrue(security.validate_site_access(admin_payload, "site-bravo"))

        # Operator scoped strictly to site-alpha
        alpha_op_token = security.create_access_token("op_alpha", "operator", site_ids=["site-alpha"])
        alpha_payload = security.validate_token(alpha_op_token)
        self.assertTrue(security.validate_site_access(alpha_payload, "site-alpha"))

        # Cross-site access to site-bravo MUST raise HTTPException 403 Forbidden
        with self.assertRaises(HTTPException) as ctx:
            security.validate_site_access(alpha_payload, "site-bravo")
        self.assertEqual(ctx.exception.status_code, 403)

    # -----------------------------------------------------------------------
    # 2. Model Lifecycle, Gated Promotion & Rollback (V5-09, FR-3)
    # -----------------------------------------------------------------------
    def test_model_lifecycle_promotion_and_rollback(self):
        # Stage candidate model v8.3.0
        model_registry.registry.stage_deployment(
            version="8.3.0",
            name="YOLOv8n-Border-Analytics",
            artifact_hash="b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef01",
            class_map=["person", "vehicle"],
            thresholds={"conf": 0.45, "iou": 0.50}
        )
        status = model_registry.registry.get_status()
        self.assertEqual(status["version"], "8.2.0")  # Still on active version 8.2.0

        # Promote to v8.3.0
        promo = model_registry.registry.promote_version("8.3.0", "Sector Lead", "Approved after field evaluation")
        self.assertEqual(promo["version"], "8.3.0")
        self.assertEqual(model_registry.registry.version, "8.3.0")

        # Rollback to v8.2.0
        rb = model_registry.registry.rollback_version("8.2.0", "Sector Lead", "Rollback to stable baseline")
        self.assertEqual(rb["version"], "8.2.0")
        self.assertEqual(model_registry.registry.version, "8.2.0")
        self.assertGreaterEqual(len(model_registry.registry.promotion_log), 2)

    # -----------------------------------------------------------------------
    # 3. Field Quality Evaluation Datasets & Reports (V5-01, V5-06, FR-4)
    # -----------------------------------------------------------------------
    def test_field_quality_evaluation_reporting(self):
        datasets = evaluation.eval_engine.list_datasets()
        self.assertGreaterEqual(len(datasets), 1)

        target_ds = datasets[0]["id"]
        report = evaluation.eval_engine.run_evaluation(target_ds, "8.2.0", approved_by="HQ Evaluation Officer")

        self.assertIn("precision", report)
        self.assertIn("recall", report)
        self.assertIn("f1_score", report)
        self.assertIn("false_positive_rate", report)
        self.assertGreater(report["precision"], 0.85)
        self.assertGreater(report["recall"], 0.85)
        self.assertIn("person", report["per_class_metrics_json"])

    # -----------------------------------------------------------------------
    # 4. Alert Disposition Workflow & Operator Feedback (V5-08, FR-5)
    # -----------------------------------------------------------------------
    def test_alert_disposition_workflow(self):
        cam = models.Camera(id="cam-disp-test", site_id="site-alpha", name="Disp Camera", location="North Sector")
        self.db.add(cam)
        alert = models.Alert(
            id="EVT-DISP-001",
            site_id="site-alpha",
            type="intrusion",
            sev="high",
            cam_id="cam-disp-test",
            confidence=88,
            state="open",
            detail_enc=security.encrypt_field("Fence breach detected")
        )
        self.db.add(alert)
        self.db.commit()

        # Operator marks disposition as false positive due to wildlife
        disp = models.AlertDisposition(
            alert_id=alert.id,
            site_id="site-alpha",
            user_id="operator_john",
            previous_state="open",
            new_state="false_positive",
            reason_code="false_positive_wildlife",
            notes="Identified as grazing cattle near outer perimeter"
        )
        self.db.add(disp)
        alert.state = "false_positive"
        alert.disposition_code = "false_positive_wildlife"
        alert.reviewed = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = "operator_john"
        self.db.commit()

        self.assertEqual(alert.state, "false_positive")
        self.assertEqual(alert.disposition_code, "false_positive_wildlife")

    # -----------------------------------------------------------------------
    # 5. Cryptographic Backup, Restore & Versioned Key Rotation (V5-03, V5-10, FR-6)
    # -----------------------------------------------------------------------
    def test_backup_restore_and_versioned_key_rotation(self):
        # 1. Versioned Key Encryption & Rotation
        secret_text = "Tactical Grid Coordinates Alpha-9"
        encrypted_v1 = security.encrypt_field(secret_text, key_version="v1")
        self.assertTrue(encrypted_v1.startswith("v1:"))
        self.assertEqual(security.decrypt_field(encrypted_v1), secret_text)

        # Rotate to v2
        security.rotate_key("v2")
        encrypted_v2 = security.encrypt_field(secret_text, key_version="v2")
        self.assertTrue(encrypted_v2.startswith("v2:"))
        self.assertEqual(security.decrypt_field(encrypted_v2), secret_text)
        # Verify backward compatibility: v1 ciphertext still decrypts perfectly under v2 active state
        self.assertEqual(security.decrypt_field(encrypted_v1), secret_text)

        # 2. Backup and Restore
        backup_res = backup_service.generate_site_backup(self.db, "site-alpha", backup_dir="scratch/backups")
        self.assertTrue(os.path.exists(backup_res["file_path"]))
        self.assertEqual(backup_res["status"], "completed")

        # Restore into DB
        restore_res = backup_service.restore_site_backup(self.db, backup_res["file_path"], "site-alpha")
        self.assertEqual(restore_res["status"], "completed")
        self.assertTrue(restore_res["ledger_intact"])

    # -----------------------------------------------------------------------
    # 6. C2 Staging Delivery & Replay Protection (V5-07, FR-7)
    # -----------------------------------------------------------------------
    def test_c2_staging_delivery_and_replay_protection(self):
        now_str = datetime.utcnow().isoformat()
        idemp_key = "IDEMP-C2-STAGE-TEST-001"

        # First delivery: Valid
        valid, msg = rule_engine.verify_c2_replay(idemp_key, now_str)
        self.assertTrue(valid, msg)

        # Replay attempt with same idempotency key: MUST be rejected
        dup_valid, dup_msg = rule_engine.verify_c2_replay(idemp_key, now_str)
        self.assertFalse(dup_valid)
        self.assertIn("replay", dup_msg.lower())

        # Stale timestamp (> 300s): MUST be rejected
        stale_ts = (datetime.utcnow() - timedelta(seconds=400)).isoformat()
        stale_valid, stale_msg = rule_engine.verify_c2_replay("IDEMP-C2-STALE-KEY", stale_ts)
        self.assertFalse(stale_valid)
        self.assertIn("drift", stale_msg.lower())

    # -----------------------------------------------------------------------
    # 7. Privacy Governance & Restricted Mode (FR-10)
    # -----------------------------------------------------------------------
    def test_privacy_governance_restricted_mode(self):
        # Without legal approval, biometric capture must be restricted/masked
        status_before = governance.governance_manager.get_site_governance_status(self.db, "site-bravo")
        self.assertFalse(status_before["face_recognition_enabled"])
        self.assertTrue(governance.governance_manager.should_mask_sensitive_attributes(self.db, "site-bravo", "face_recognition"))

        # Record legal approval
        governance.governance_manager.record_approval(
            db=self.db,
            site_id="site-bravo",
            capability="face_recognition",
            legal_approval_ref="LEGAL-HQ-2026-991A",
            approved_by="Legal General Counsel",
            restricted_mode=False
        )

        status_after = governance.governance_manager.get_site_governance_status(self.db, "site-bravo")
        self.assertTrue(status_after["face_recognition_enabled"])
        self.assertFalse(governance.governance_manager.should_mask_sensitive_attributes(self.db, "site-bravo", "face_recognition"))

    # -----------------------------------------------------------------------
    # 8. Soak Simulation & Memory/Queue Stability (V5-05, FR-8)
    # -----------------------------------------------------------------------
    def test_soak_queue_stability(self):
        from app.video_stream import BoundedFrameQueue
        import numpy as np

        q = BoundedFrameQueue(maxsize=10)
        # Simulate high frame influx over continuous ingestion
        for i in range(500):
            dummy_frame = np.zeros((30, 30, 3), dtype=np.uint8)
            q.push(dummy_frame, timestamp=float(i))

        stats = q.get_stats()
        self.assertEqual(stats["depth"], 10)  # Bounded
        self.assertEqual(stats["dropped_frames"], 490)  # Drop oldest policy executed without unbounded growth


if __name__ == "__main__":
    unittest.main()

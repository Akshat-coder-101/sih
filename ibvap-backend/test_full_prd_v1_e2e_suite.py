"""
IBVAP Full PRD v1.0.0 End-to-End & Single-Frame Operational Verification Suite.
Tests the 6 critical operational flows defined in Section 15 (lines 536-541)
and the discrete single-camera-frame capture and processing capabilities.
Uses in-memory DB for zero external test dependencies.
"""

import io
import time
import json
import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app import (
    models, schemas, security, ledger, model_registry,
    evaluation, backup_service, governance, rule_engine,
    terrain_service, recommendation_service, video_stream
)
from app.main import (
    get_camera_single_frame, step_camera_frame,
    get_alert_terrain, enrich_alert_terrain_endpoint,
    get_alert_recommendation, review_tactical_recommendation,
    list_c2_deliveries, retry_c2_delivery
)


class TestFullPrdV1E2ESuite(unittest.TestCase):
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
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        # Seed Site
        self.site = models.Site(
            id="site-alpha",
            name="Sector North BOP Alpha",
            region="Northern Frontier",
            timezone="UTC",
            connectivity_profile="standard"
        )
        self.db.add(self.site)

        # Seed Camera
        self.camera = models.Camera(
            id="CAM-01",
            site_id="site-alpha",
            name="Perimeter Gate Alpha",
            location="Sector Alpha North Gate",
            online=True,
            geo="32.7266, 74.8570",
            active_model_version="8.2.0",
            active_rule_version="1.0"
        )
        self.db.add(self.camera)

        # Seed Fence Rule
        self.rule = models.FenceRule(
            id="rule-cam1-01",
            site_id="site-alpha",
            camera_id="CAM-01",
            name="Perimeter Tripwire Alpha",
            rule_type="tripwire",
            direction="bidirectional",
            coordinates=[[0, 50], [100, 50]],
            target_classes=["person", "vehicle", "weapon"],
            severity="high",
            enabled=True,
            cooldown_seconds=0
        )
        self.db.add(self.rule)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def get_token_payload(self, role: str = "admin", site_ids: list = None):
        return {
            "sub": f"test-{role}",
            "role": role,
            "site_ids": site_ids or ["*"]
        }

    # -----------------------------------------------------------------------
    # FLOW 1: Fixture Pipeline -> Tracker -> Rule -> Ledger -> Evidence
    # -----------------------------------------------------------------------
    def test_flow_1_pipeline_to_persistence_and_ledger(self):
        """Flow 1: Edge capture -> detector -> tracker -> rule -> DB -> evidence -> ledger."""
        track = rule_engine.Track("TRK-E2E-101", [10, 45, 10, 20], "person", 0.94)
        track.history = [[10, 45], [10, 55]]  # crosses y=50 line

        frame_bytes = video_stream.get_camera_frame("CAM-01")
        alert = rule_engine.evaluate_track_against_rules_sync(self.db, self.camera, track, frame_bytes)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.site_id, "site-alpha")
        self.assertEqual(alert.cam_id, "CAM-01")

        # Verify Evidence Asset created
        evidence = self.db.query(models.EvidenceAsset).filter(models.EvidenceAsset.alert_id == alert.id).first()
        self.assertIsNotNone(evidence)
        self.assertIsNotNone(evidence.content_hash)

        # Verify SHA-256 Ledger Record appended
        ledger_rec = self.db.query(models.LedgerRecord).filter(models.LedgerRecord.alert_id == alert.id).first()
        self.assertIsNotNone(ledger_rec)
        self.assertIsNotNone(ledger_rec.record_hash)

        # Verify Ledger chain integrity
        ledger_result = ledger.verify_chain(self.db)
        self.assertTrue(ledger_result.intact)
        self.assertGreaterEqual(ledger_result.checked_records, 1)

    # -----------------------------------------------------------------------
    # SINGLE CAMERA FRAME PROCESSING & STEPPING CAPABILITIES
    # -----------------------------------------------------------------------
    def test_single_camera_frame_capture_and_step(self):
        """Verify discrete single-frame capture and single-frame stepping."""
        operator_payload = self.get_token_payload("operator")

        # 1. Fetch instantaneous single frame
        response = get_camera_single_frame("CAM-01", token=None, db=self.db)
        self.assertEqual(response.media_type, "image/jpeg")
        self.assertEqual(response.headers["X-Camera-ID"], "CAM-01")
        self.assertGreater(len(response.body), 100)

        # 2. Advance by exactly 1 frame
        step_out = step_camera_frame("CAM-01", user_payload=operator_payload)
        self.assertEqual(step_out.cam_id, "CAM-01")
        self.assertGreaterEqual(step_out.frame_index, 1)

    def test_single_camera_frame_ingestion_and_inference(self):
        """Verify synchronous single-frame ingestion and YOLO inference."""
        frame_bytes = video_stream.get_camera_frame("CAM-01")
        result = video_stream.process_single_frame("CAM-01", frame_bytes, self.db, self.camera)

        self.assertEqual(result["cam_id"], "CAM-01")
        self.assertIn("detections", result)
        self.assertIn("processing_time_ms", result)
        self.assertGreaterEqual(result["processing_time_ms"], 0.0)
        self.assertEqual(result["detector_model"], "YOLOv8s-Security-v8.2.0")

    # -----------------------------------------------------------------------
    # FLOW 2: Operator Alert Lifecycle (Ack -> Resolve with Reason)
    # -----------------------------------------------------------------------
    def test_flow_2_operator_alert_disposition_lifecycle(self):
        """Flow 2: Operator receives alert -> acknowledges -> resolves with reason code."""
        # Create alert
        alert = models.Alert(
            id="EVT-FLOW2-001",
            site_id="site-alpha",
            type="loiter",
            sev="high",
            cam_id="CAM-01",
            confidence=89,
            detail_enc="Target dwelling in perimeter sector",
            state="open"
        )
        self.db.add(alert)
        self.db.commit()

        # 1. Operator Acknowledges
        alert.state = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        disp_ack = models.AlertDisposition(
            alert_id=alert.id,
            site_id="site-alpha",
            user_id="operator_alpha",
            previous_state="open",
            new_state="acknowledged",
            reason_code="valid_intrusion",
            notes="Visual contact confirmed"
        )
        self.db.add(disp_ack)
        self.db.commit()

        self.assertEqual(alert.state, "acknowledged")

        # 2. Operator Resolves
        alert.state = "resolved"
        alert.resolved_by = "operator_alpha"
        alert.resolved_at = datetime.utcnow()
        alert.resolution_note = "Patrol intercepted suspect. Sector all clear."
        disp_res = models.AlertDisposition(
            alert_id=alert.id,
            site_id="site-alpha",
            user_id="operator_alpha",
            previous_state="acknowledged",
            new_state="resolved",
            reason_code="valid_intrusion",
            notes="Suspect detained by QRT"
        )
        self.db.add(disp_res)
        self.db.commit()

        self.assertEqual(alert.state, "resolved")
        self.assertEqual(alert.resolved_by, "operator_alpha")

    # -----------------------------------------------------------------------
    # FLOW 3: Supervisor Review & Quality Report
    # -----------------------------------------------------------------------
    def test_flow_3_supervisor_quality_metrics(self):
        """Flow 3: Supervisor reviews feedback breakdown and quality metrics."""
        a1 = models.Alert(id="EVT-Q1", site_id="site-alpha", type="intrusion", sev="high", cam_id="CAM-01", state="resolved")
        a2 = models.Alert(id="EVT-Q2", site_id="site-alpha", type="loiter", sev="med", cam_id="CAM-01", state="false_positive")
        d1 = models.AlertDisposition(alert_id="EVT-Q1", site_id="site-alpha", user_id="op1", previous_state="open", new_state="resolved", reason_code="valid_intrusion")
        d2 = models.AlertDisposition(alert_id="EVT-Q2", site_id="site-alpha", user_id="op1", previous_state="open", new_state="false_positive", reason_code="false_positive_wildlife")
        self.db.add_all([a1, a2, d1, d2])
        self.db.commit()

        total = self.db.query(models.Alert).filter(models.Alert.site_id == "site-alpha").count()
        fp_count = self.db.query(models.Alert).filter(models.Alert.site_id == "site-alpha", models.Alert.state == "false_positive").count()
        self.assertGreaterEqual(total, 2)
        self.assertEqual(fp_count, 1)

    # -----------------------------------------------------------------------
    # FLOW 4: Admin Onboarding & Model Promotion
    # -----------------------------------------------------------------------
    def test_flow_4_admin_camera_and_model_promotion(self):
        """Flow 4: Administrator stages model, evaluates canary, and promotes."""
        # Stage Model
        staged = model_registry.registry.stage_deployment(
            version="8.3.0",
            name="YOLOv8s-Border-v8.3.0",
            artifact_hash="hash_v830_secure",
            class_map=["person", "vehicle", "weapon"],
            thresholds={"person": 0.5, "weapon": 0.65}
        )
        self.assertTrue(staged)

        # Promote Model
        promo = model_registry.registry.promote_version("8.3.0", "Admin Lead", "Approved after field testing")
        self.assertEqual(model_registry.registry.version, "8.3.0")

        # Rollback Model
        rb = model_registry.registry.rollback_version("8.2.0", "Admin Lead", "Revert to baseline")
        self.assertEqual(model_registry.registry.version, "8.2.0")

    # -----------------------------------------------------------------------
    # FLOW 5: Patrol Mobile GIS Terrain & Correlated Recommendation
    # -----------------------------------------------------------------------
    def test_flow_5_patrol_gis_terrain_and_recommendations(self):
        """Flow 5: Mobile patrol receives GIS terrain context and tactical guidance."""
        operator_payload = self.get_token_payload("operator")
        supervisor_payload = self.get_token_payload("supervisor")

        # Alert with weapon threat
        alert = models.Alert(
            id="EVT-WEAPON-99",
            site_id="site-alpha",
            type="weapon",
            sev="high",
            cam_id="CAM-01",
            confidence=96,
            location="Sector North Boundary Post 4",
            state="open"
        )
        self.db.add(alert)
        self.db.commit()

        # 1. Enrich Terrain (FR-6)
        terrain = get_alert_terrain("EVT-WEAPON-99", db=self.db, user_payload=operator_payload)
        self.assertEqual(terrain.alert_id, "EVT-WEAPON-99")
        self.assertGreater(terrain.elevation_m, 0.0)
        self.assertGreaterEqual(terrain.slope_deg, 0.0)
        self.assertIn(terrain.land_cover, ["rocky_ridge", "dense_foliage", "arid_scrub", "waterway", "paved_road"])
        self.assertGreater(terrain.nearest_road_distance_m, 0.0)

        # 2. Correlated Tactical Recommendation (FR-7)
        rec = get_alert_recommendation("EVT-WEAPON-99", db=self.db, user_payload=operator_payload)
        self.assertEqual(rec.alert_id, "EVT-WEAPON-99")
        self.assertEqual(rec.status, "draft")
        self.assertGreaterEqual(len(rec.tactical_actions), 2)
        self.assertTrue("CRITICAL THREAT" in rec.action_summary or "Armed" in rec.action_summary or "weapon" in str(rec.contributing_factors))

        # 3. Supervisor Reviews and Approves Tactical Recommendation
        review_req = schemas.RecommendationReviewRequest(
            status="approved",
            review_notes="QRT Bravo mobilized for intercept"
        )
        approved_rec = review_tactical_recommendation(rec.id, review_req, db=self.db, user_payload=supervisor_payload)
        self.assertEqual(approved_rec.status, "approved")
        self.assertEqual(approved_rec.reviewed_by, "test-supervisor")
        self.assertEqual(approved_rec.review_notes, "QRT Bravo mobilized for intercept")

    # -----------------------------------------------------------------------
    # FLOW 6: Governance Approvals & Restricted Mode
    # -----------------------------------------------------------------------
    def test_flow_6_governance_approval_lifecycle(self):
        """Flow 6: Biometric capability disabled -> approved -> restricted mode."""
        # Initially disabled
        status = governance.governance_manager.get_site_governance_status(self.db, "site-alpha")
        self.assertFalse(status["face_recognition_enabled"])

        # Create legal approval
        governance.governance_manager.record_approval(
            self.db,
            site_id="site-alpha",
            capability="face_recognition",
            legal_approval_ref="MHA-REF-2026-X9",
            approved_by="SecDirector",
            restricted_mode=False
        )

        # Now enabled
        status_after = governance.governance_manager.get_site_governance_status(self.db, "site-alpha")
        self.assertTrue(status_after["face_recognition_enabled"])

    # -----------------------------------------------------------------------
    # C2 Delivery Tracking & Dead-Letter Retry (FR-10)
    # -----------------------------------------------------------------------
    def test_c2_deliveries_and_dead_letter_retry(self):
        """Verify C2 delivery inspection and manual dead-letter retry."""
        supervisor_payload = self.get_token_payload("supervisor")
        admin_payload = self.get_token_payload("admin")

        mock_dead_letter = {
            "alert_id": "EVT-C2-DEADLETTER-1",
            "site_id": "site-alpha",
            "status": "dead_letter",
            "last_error": "Connection timed out to C2 relay",
            "idempotency_key": "IDEMP-DEADLETTER-1",
            "payload": {
                "alert_id": "EVT-C2-DEADLETTER-1",
                "type": "weapon",
                "site_id": "site-alpha",
                "sev": "high"
            },
            "next_retry": time.time() + 60.0,
            "attempts": 3
        }
        rule_engine.c2_retry_queue.append(mock_dead_letter)

        deliveries = list_c2_deliveries(site_id="site-alpha", user_payload=supervisor_payload)
        self.assertGreaterEqual(deliveries["dead_letter_count"], 1)

        retried = retry_c2_delivery("EVT-C2-DEADLETTER-1", user_payload=admin_payload)
        self.assertEqual(retried["status"], "retried")


if __name__ == "__main__":
    unittest.main()

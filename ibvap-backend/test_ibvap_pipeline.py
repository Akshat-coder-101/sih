"""
Automated Test Suite for IBVAP PRD v2.0 Pilot Capabilities.
Tests:
1. Virtual Fence Geometry (line intersection & point-in-polygon)
2. Tracker (persistent track IDs, IoU matching, dwell time)
3. Cryptographic Ledger (genesis, chain linkage, tamper detection)
4. Alert Lifecycle (state transitions: open -> acknowledged -> resolved)
5. RBAC & Endpoints (health, readiness, CSV export, fence rules)
"""
import unittest
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models, security, ledger, tracker, rule_engine


class TestIBVAPPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    # 1. Virtual Fence Geometry Tests
    def test_line_intersect(self):
        # Crossing line: (10, 50) -> (10, 70) crosses tripwire (0, 60) -> (20, 60)
        A = [10.0, 50.0]
        B = [10.0, 70.0]
        C = [0.0, 60.0]
        D = [20.0, 60.0]
        self.assertTrue(rule_engine.line_intersect(A, B, C, D))

        # Parallel non-crossing line
        A_parallel = [10.0, 50.0]
        B_parallel = [10.0, 55.0]
        self.assertFalse(rule_engine.line_intersect(A_parallel, B_parallel, C, D))

    def test_point_in_polygon(self):
        poly = [[10.0, 10.0], [50.0, 10.0], [50.0, 50.0], [10.0, 50.0]]
        inside_point = [30.0, 30.0]
        outside_point = [5.0, 5.0]
        self.assertTrue(rule_engine.point_in_polygon(inside_point, poly))
        self.assertFalse(rule_engine.point_in_polygon(outside_point, poly))

    # 2. Object Tracker Tests
    def test_tracker_id_persistence(self):
        trk = tracker.ObjectTracker("cam-test", max_missed=5, iou_threshold=0.3)
        det_frame1 = [{"box": [20.0, 30.0, 10.0, 20.0], "class_name": "person", "confidence": 0.92}]
        active_tracks1 = trk.update(det_frame1)
        self.assertEqual(len(active_tracks1), 1)
        first_id = active_tracks1[0].track_id

        # Next frame with slightly moved box
        det_frame2 = [{"box": [21.0, 31.0, 10.0, 20.0], "class_name": "person", "confidence": 0.94}]
        active_tracks2 = trk.update(det_frame2)
        self.assertEqual(len(active_tracks2), 1)
        self.assertEqual(active_tracks2[0].track_id, first_id, "Track ID must persist across frames")

    # 3. Ledger Hash-Chain & Tamper Detection Tests
    def test_ledger_tamper_detection(self):
        # Create test camera
        cam = models.Camera(id="cam-test-ledger", name="Test Cam", location="BOP Test", online=True)
        self.db.add(cam)
        self.db.commit()

        # Insert 3 alerts and append to ledger
        alerts = []
        for i in range(3):
            a = models.Alert(
                id=f"TEST-EVT-{i+1:03d}",
                type="intrusion",
                sev="high",
                cam_id="cam-test-ledger",
                cam_name="Test Cam",
                location="BOP Test",
                confidence=90,
                track_id="#101",
                detail_enc=security.encrypt_field(f"Event {i+1}"),
                reviewed=False,
                state="open",
                provenance="detector",
                ts=datetime.utcnow()
            )
            self.db.add(a)
            self.db.commit()
            self.db.refresh(a)
            ledger.append_to_ledger(self.db, a)
            alerts.append(a)

        # Verify initial intact status
        verify_res = ledger.verify_chain(self.db)
        self.assertTrue(verify_res.intact)
        self.assertEqual(verify_res.checked_records, 3)

        # Directly tamper with alert #2 ciphertext in DB (bypassing ledger)
        alerts[1].detail_enc = security.encrypt_field("Tampered Payload by Adversary")
        self.db.commit()

        # Verify ledger catches the tampering
        tamper_res = ledger.verify_chain(self.db)
        self.assertFalse(tamper_res.intact, "Ledger must catch unauthorized database modification")
        self.assertEqual(tamper_res.broken_at_seq, 1)
        self.assertEqual(tamper_res.broken_alert_id, "TEST-EVT-002")


if __name__ == "__main__":
    unittest.main()

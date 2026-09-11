"""
Contract and regression test suite verifying backend contracts for dynamic frontend operation:
- /metrics response schema and snake_case worker telemetry
- /ready response schema and model_loaded / active_streams fields
- /cameras metadata completeness (geo, location, name, priority, online)
- Camera toggle mutation contract (authoritative updated state)
- Alert camera metadata tie and provenance integrity
"""
import unittest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import Response

from app.database import Base
from app import models, schemas, security
from app.main import list_cameras, toggle_camera, get_metrics, ready, list_alerts, camera_to_out


class TestDynamicDataContract(unittest.TestCase):
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
        # Ensure site exists
        if not self.db.query(models.Site).filter(models.Site.id == "site-alpha").first():
            self.db.add(models.Site(id="site-alpha", name="BOP Alpha", region="North", retention_days=90))
            self.db.commit()

        # Ensure cameras exist
        if self.db.query(models.Camera).count() == 0:
            c1 = models.Camera(
                id="cam-1",
                site_id="site-alpha",
                name="CAM-01 · North Perimeter",
                location="BOP Alpha — North Fence Line",
                online=True,
                priority="High",
                fps=9,
                night=False,
                scene="fence",
                geo="29.5481°N 74.8763°E",
                anchor={"left": 44, "top": 46, "w": 9, "h": 26},
                rtsp_url="rtsp://cam-1.bop.local:554/stream1"
            )
            c2 = models.Camera(
                id="cam-2",
                site_id="site-alpha",
                name="CAM-02 · Check Post Gate",
                location="BOP Alpha — Gate Road",
                online=True,
                priority="Medium",
                fps=8,
                night=False,
                scene="gate",
                geo="29.5502°N 74.8791°E",
                anchor={"left": 41, "top": 52, "w": 20, "h": 24},
                rtsp_url="rtsp://cam-2.bop.local:554/stream2"
            )
            self.db.add_all([c1, c2])
            self.db.commit()

        # Ensure sample alert exists
        if self.db.query(models.Alert).count() == 0:
            a = models.Alert(
                id="EVT-0001",
                site_id="site-alpha",
                type="intrusion",
                sev="high",
                cam_id="cam-1",
                cam_name="CAM-01 · North Perimeter",
                location="BOP Alpha — North Fence Line",
                confidence=95,
                track_id="#101",
                detail_enc=security.encrypt_field("Person crossed north fence line"),
                reviewed=False,
                state="open",
                provenance="detector",
                rule_id="rule-cam-1-01",
                rule_version="1.0",
                ts=datetime.utcnow()
            )
            self.db.add(a)
            self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_metrics_contract(self):
        """Verify get_metrics provides worker_telemetry, camera_workers, and model_registry."""
        user = {"sub": "operator", "role": "operator", "site_id": "site-alpha"}
        data = get_metrics(site_id="site-alpha", db=self.db, user_payload=user)
        self.assertIn("timestamp", data)
        self.assertIn("total_alerts", data)
        self.assertIn("camera_workers", data)
        self.assertIn("worker_telemetry", data)
        self.assertIn("model_registry", data)
        self.assertIsInstance(data["worker_telemetry"], dict)

    def test_readiness_contract(self):
        """Verify ready route returns model_loaded, database, camera_workers, and active_streams."""
        res = Response()
        status = ready(response=res, db=self.db)
        self.assertTrue(hasattr(status, "database"))
        self.assertTrue(hasattr(status, "model_loaded"))
        self.assertTrue(hasattr(status, "camera_workers"))
        self.assertTrue(hasattr(status, "active_streams"))
        self.assertIsInstance(status.active_streams, list)

    def test_degraded_readiness_returns_503_with_complete_payload(self):
        """Verify ready route sets status 503 when degraded but preserves structured response payload."""
        from app import model_registry
        orig_loaded = model_registry.registry.is_loaded
        try:
            model_registry.registry.is_loaded = False
            res = Response()
            status = ready(response=res, db=self.db)
            self.assertEqual(res.status_code, 503)
            self.assertFalse(status.ready)
            self.assertTrue(status.database)
            self.assertFalse(status.model_loaded)
            self.assertIsInstance(status.camera_workers, int)
            self.assertIsInstance(status.active_streams, list)
            self.assertIsNotNone(status.timestamp)
        finally:
            model_registry.registry.is_loaded = orig_loaded

    def test_cameras_metadata_contract(self):
        """Verify list_cameras returns authoritative camera fields required by frontend."""
        user = {"sub": "operator", "role": "operator", "site_id": "site-alpha"}
        cams = list_cameras(site_id="site-alpha", db=self.db, user_payload=user)
        self.assertGreaterEqual(len(cams), 1)
        for c in cams:
            self.assertTrue(c.id)
            self.assertTrue(c.name)
            self.assertTrue(c.location)
            self.assertTrue(c.geo)
            self.assertIn("°", c.geo)
            self.assertIn(c.priority, ["High", "Medium", "Low"])
            self.assertIsInstance(c.online, bool)
            self.assertIsInstance(c.fps, int)

    def test_camera_toggle_mutation_contract(self):
        """Verify toggle_camera accurately toggles camera state and returns updated entity."""
        user = {"sub": "admin", "role": "admin", "site_id": "site-alpha"}
        target = self.db.query(models.Camera).filter(models.Camera.id == "cam-1").first()
        initial_online = target.online

        # Toggle state
        updated = toggle_camera("cam-1", db=self.db, user_payload=user)
        self.assertEqual(updated.id, "cam-1")
        self.assertEqual(updated.online, not initial_online)

        # Toggle back
        restored = toggle_camera("cam-1", db=self.db, user_payload=user)
        self.assertEqual(restored.online, initial_online)

    def test_alert_provenance_and_camera_metadata_tie(self):
        """Verify alerts returned from backend retain camera identification and provenance."""
        user = {"sub": "operator", "role": "operator", "site_id": "site-alpha"}
        alerts = list_alerts(site_id=None, cam_id=None, db=self.db, user_payload=user, offset=0, limit=100)
        self.assertGreaterEqual(len(alerts), 1)
        first = alerts[0]
        self.assertEqual(first.cam_id, "cam-1")
        self.assertEqual(first.provenance, "detector")
        self.assertEqual(first.state, "open")

    def test_camera_capability_and_source_contract(self):
        """Verify camera outputs expose source_type and supports_webcam capabilities."""
        user = {"sub": "operator", "role": "operator", "site_id": "site-alpha"}
        cams = list_cameras(site_id="site-alpha", db=self.db, user_payload=user)
        self.assertGreaterEqual(len(cams), 2)
        cam_map = {c.id: c for c in cams}
        self.assertIn("cam-1", cam_map)
        self.assertIn("cam-2", cam_map)
        # Verify supports_webcam is boolean and source_type is string
        self.assertTrue(cam_map["cam-1"].supports_webcam)
        self.assertEqual(cam_map["cam-1"].source_type, "webcam")
        self.assertFalse(cam_map["cam-2"].supports_webcam)
        self.assertEqual(cam_map["cam-2"].source_type, "rtsp")

    def test_camera_missing_version_resilience(self):
        """Verify camera_to_out does not fabricate an active model version when absent."""
        mock_cam = models.Camera(
            id="cam-custom",
            site_id="site-alpha",
            name="CAM-Custom · Unassigned Model",
            location="BOP Custom",
            online=True,
            priority="Low",
            fps=5,
            night=False,
            scene="fence",
            geo="29.0°N 74.0°E",
            anchor={"left": 10, "top": 10, "w": 10, "h": 10},
            rtsp_url="rtsp://custom:554/stream",
            active_model_version=None,
            active_rule_version=None
        )
        out = camera_to_out(mock_cam)
        self.assertIsNone(out.active_model_version)
        self.assertIsNone(out.active_rule_version)

    def test_simulation_alert_provenance_contract(self):
        """Verify simulation alerts retain provenance='simulation'."""
        sim_alert = models.Alert(
            id="EVT-SIM-01",
            site_id="site-alpha",
            type="intrusion",
            sev="low",
            cam_id="cam-2",
            cam_name="CAM-02 · Check Post Gate",
            location="BOP Alpha — Gate Road",
            confidence=80,
            track_id="#202",
            detail_enc=security.encrypt_field("Simulated benchmark alert"),
            reviewed=False,
            state="open",
            provenance="simulation",
            rule_id="rule-sim",
            ts=datetime.utcnow()
        )
        self.db.add(sim_alert)
        self.db.commit()

        user = {"sub": "operator", "role": "operator", "site_id": "site-alpha"}
        alerts = list_alerts(site_id=None, cam_id="cam-2", db=self.db, user_payload=user, offset=0, limit=10)
        self.assertTrue(any(a.id == "EVT-SIM-01" and a.provenance == "simulation" for a in alerts))


import unittest
import hashlib
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.database import Base
from app import models, schemas, security, ledger, blockchain_provider
from app import merkle_engine, provenance_service, multisig_service
from app.main import (
    get_alert_merkle_proof,
    verify_merkle_proof_endpoint,
    get_model_provenance,
    get_alert_provenance,
    verify_alert_provenance_endpoint,
    create_proposal_endpoint,
    get_proposals_endpoint,
    get_proposal_endpoint,
    sign_proposal_endpoint,
    reject_proposal_endpoint,
    submit_proposal_endpoint,
    verify_proposal_endpoint,
)


class TestAdvancedBlockchainIntegritySuite(unittest.TestCase):
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

        # Seed site
        if not self.db.query(models.Site).filter(models.Site.id == "site-alpha").first():
            self.db.add(models.Site(id="site-alpha", name="BOP Alpha", region="North", retention_days=90))
            self.db.commit()

        # Seed camera
        if not self.db.query(models.Camera).filter(models.Camera.id == "cam-1").first():
            cam = models.Camera(id="cam-1", site_id="site-alpha", name="North Gate PTZ", location="BOP Alpha Gate")
            self.db.add(cam)
            self.db.commit()

        # Clean tables
        self.db.query(models.AnchorSignature).delete()
        self.db.query(models.MerkleAnchor).delete()
        self.db.query(models.ModelProvenance).delete()
        self.db.query(models.LedgerAnchor).delete()
        self.db.query(models.LedgerRecord).delete()
        self.db.query(models.Alert).delete()
        self.db.commit()

        # Seed 4 alerts with ledger records & provenance
        self.alerts = []
        for i in range(4):
            alert = models.Alert(
                id=f"ALT-ADV-{i}",
                site_id="site-alpha",
                cam_id="cam-1",
                cam_name="North Gate PTZ",
                location="BOP Alpha Gate",
                type="intrusion",
                sev="high",
                confidence=92 + i,
                track_id=f"TRK-{200 + i}",
                detail_enc=security.encrypt_field(f"Confidential intel {i}"),
                provenance="detector" if i < 3 else "simulation",
                ts=datetime.utcnow(),
            )
            # Attach model provenance
            provenance_service.attach_alert_provenance(
                alert,
                self.db,
                is_simulation=(alert.provenance == "simulation"),
            )
            self.db.add(alert)
            self.db.flush()

            # Record in local ledger
            ledger.append_to_ledger(self.db, alert)
            self.alerts.append(alert)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    # =========================================================================
    # PART 1: DETERMINISTIC MERKLE PROOFS (FR-MP-1, FR-MP-2, FR-MP-3)
    # =========================================================================

    def test_merkle_canonical_leaf_hashing(self):
        """Canonical leaf serialization must be strictly deterministic across keys order."""
        leaf_1 = merkle_engine.build_canonical_leaf_payload(
            site_id="site-alpha",
            sequence=0,
            alert_id="ALT-1",
            record_hash="a" * 64,
            model_provenance_hash="b" * 64,
            rule_config_hash="c" * 64,
        )
        hash_1 = merkle_engine.compute_leaf_hash(leaf_1)
        self.assertEqual(len(hash_1), 64)

        # Re-hashing the identical payload yields identical hash
        hash_2 = merkle_engine.compute_leaf_hash(leaf_1)
        self.assertEqual(hash_1, hash_2)

    def test_merkle_tree_construction_and_proof(self):
        """Builds Merkle tree over sequence range and produces valid inclusion proofs."""
        leaf_hashes = []
        for i in range(4):
            lp = merkle_engine.build_canonical_leaf_payload(
                site_id="site-alpha",
                sequence=i,
                alert_id=self.alerts[i].id,
                record_hash=f"record_hash_{i}",
                model_provenance_hash=self.alerts[i].provenance_hash,
                rule_config_hash=self.alerts[i].rule_config_hash,
            )
            leaf_hashes.append(merkle_engine.compute_leaf_hash(lp))

        root_hash, levels = merkle_engine.build_merkle_tree(leaf_hashes)
        self.assertEqual(len(levels[0]), 4)
        self.assertEqual(len(root_hash), 64)

        # Test inclusion proof for each alert
        for i in range(4):
            siblings, positions = merkle_engine.generate_merkle_proof(leaf_hashes, i)
            valid, calc_root = merkle_engine.verify_merkle_proof(
                leaf_hash=leaf_hashes[i],
                sibling_hashes=siblings,
                positions=positions,
                root_hash=root_hash,
            )
            self.assertTrue(valid)
            self.assertEqual(calc_root, root_hash)

    def test_merkle_tamper_detection(self):
        """Proof verification fails if leaf, sibling, position, or root is tampered."""
        leaf_hashes = [f"{'a' * 63}{i}" for i in range(4)]
        root_hash, _ = merkle_engine.build_merkle_tree(leaf_hashes)
        siblings, positions = merkle_engine.generate_merkle_proof(leaf_hashes, 1)

        # 1. Tampered leaf hash
        tampered_leaf = "f" * 64
        valid1, _ = merkle_engine.verify_merkle_proof(
            leaf_hash=tampered_leaf,
            sibling_hashes=siblings,
            positions=positions,
            root_hash=root_hash,
        )
        self.assertFalse(valid1)

        # 2. Tampered sibling hash
        tampered_siblings = list(siblings)
        tampered_siblings[0] = "e" * 64
        valid2, _ = merkle_engine.verify_merkle_proof(
            leaf_hash=leaf_hashes[1],
            sibling_hashes=tampered_siblings,
            positions=positions,
            root_hash=root_hash,
        )
        self.assertFalse(valid2)

        # 3. Inverted position
        inverted_positions = ["left" if p == "right" else "right" for p in positions]
        valid3, _ = merkle_engine.verify_merkle_proof(
            leaf_hash=leaf_hashes[1],
            sibling_hashes=siblings,
            positions=inverted_positions,
            root_hash=root_hash,
        )
        self.assertFalse(valid3)

        # 4. Wrong root
        valid4, _ = merkle_engine.verify_merkle_proof(
            leaf_hash=leaf_hashes[1],
            sibling_hashes=siblings,
            positions=positions,
            root_hash="0" * 64,
        )
        self.assertFalse(valid4)

    # =========================================================================
    # PART 2: AI MODEL & RULE PROVENANCE (FR-MP-4, FR-MP-5)
    # =========================================================================

    def test_model_provenance_registration_and_retrieval(self):
        """Model provenance can be retrieved or registered."""
        prov = provenance_service.get_or_register_model_provenance(self.db, "8.2.0")
        self.assertIsNotNone(prov)
        self.assertEqual(prov.model_version, "8.2.0")
        self.assertEqual(len(prov.provenance_hash), 64)

    def test_simulation_vs_detector_provenance_discrimination(self):
        """Simulation alerts enforce synthetic provenance and refuse to fabricate weights."""
        detector_alert = self.alerts[0]
        self.assertEqual(detector_alert.provenance, "detector")
        self.assertNotEqual(detector_alert.model_artifact_hash, "sim-synthetic-artifact-no-detector-weights")

        sim_alert = self.alerts[3]
        self.assertEqual(sim_alert.provenance, "simulation")
        self.assertEqual(sim_alert.model_name, "Synthetic-Simulation-Engine")
        self.assertEqual(sim_alert.model_artifact_hash, "sim-synthetic-artifact-no-detector-weights")

        # Verify alert provenance integrity
        matches_det, _, _, _ = provenance_service.verify_alert_provenance(detector_alert)
        self.assertTrue(matches_det)

        matches_sim, _, _, _ = provenance_service.verify_alert_provenance(sim_alert)
        self.assertTrue(matches_sim)

    def test_provenance_tampering_detection(self):
        """Altering the stored provenance metadata invalidates verification."""
        alert = self.alerts[1]
        alert.model_artifact_hash = "tampered_artifact_hash"
        self.db.commit()

        matches, _, _, msg = provenance_service.verify_alert_provenance(alert)
        self.assertFalse(matches)
        self.assertIn("tamper detected", msg.lower())

    # =========================================================================
    # PART 3: MULTISIGNATURE ANCHORING (FR-MS-1 to FR-MS-4)
    # =========================================================================

    def test_multisig_proposal_lifecycle_and_threshold_gating(self):
        """2-of-3 threshold multisignature proposal lifecycle."""
        # 1. Admin creates proposal
        proposal = multisig_service.create_anchor_proposal(
            self.db,
            site_id="site-alpha",
            from_seq=0,
            through_seq=3,
            created_by="admin-user-1",
            expires_in_hours=24,
        )
        self.assertEqual(proposal.status, "proposed")
        self.assertEqual(multisig_service.DEFAULT_THRESHOLD, 2)
        self.assertEqual(len(proposal.signatures), 0)

        # 2. Unauthorized role (operator) cannot sign
        with self.assertRaises(PermissionError):
            multisig_service.sign_anchor_proposal(
                self.db,
                proposal_id=proposal.id,
                signer_user_id="op-1",
                signer_role="operator",
            )

        # 3. First signature by Supervisor
        p_signed_1, _ = multisig_service.sign_anchor_proposal(
            self.db,
            proposal_id=proposal.id,
            signer_user_id="sup-1",
            signer_role="supervisor",
        )
        self.assertEqual(p_signed_1.status, "partially_signed")
        self.assertEqual(len(p_signed_1.signatures), 1)

        # 4. Attempting to submit with only 1/2 signatures fails
        with self.assertRaises(ValueError) as ctx:
            multisig_service.submit_anchor_proposal(
                self.db,
                proposal_id=proposal.id,
                admin_user_id="admin-user-1",
            )
        self.assertIn("threshold not met", str(ctx.exception).lower())

        # 5. Duplicate signature by the same supervisor is rejected
        with self.assertRaises(ValueError) as ctx:
            multisig_service.sign_anchor_proposal(
                self.db,
                proposal_id=proposal.id,
                signer_user_id="sup-1",
                signer_role="supervisor",
            )
        self.assertIn("already signed", str(ctx.exception))

        # 6. Second signature by Admin satisfies threshold
        p_signed_2, _ = multisig_service.sign_anchor_proposal(
            self.db,
            proposal_id=proposal.id,
            signer_user_id="admin-user-2",
            signer_role="admin",
        )
        self.assertEqual(p_signed_2.status, "approved")
        self.assertEqual(len(p_signed_2.signatures), 2)

        # 7. Admin submits approved proposal to blockchain
        p_submitted = multisig_service.submit_anchor_proposal(
            self.db,
            proposal_id=proposal.id,
            admin_user_id="admin-user-1",
        )
        self.assertIn(p_submitted.status, ["submitted", "confirmed"])
        self.assertIsNotNone(p_submitted.transaction_hash)
        self.assertTrue(p_submitted.transaction_hash.startswith("0x"))

    def test_multisig_proposal_rejection(self):
        """Supervisor or Admin rejecting proposal terminates consensus."""
        proposal = multisig_service.create_anchor_proposal(
            self.db,
            site_id="site-alpha",
            from_seq=0,
            through_seq=2,
            created_by="admin-user-1",
        )

        # Supervisor rejects with reason
        p_rejected = multisig_service.reject_anchor_proposal(
            self.db,
            proposal_id=proposal.id,
            rejecter_user_id="sup-1",
            rejecter_role="supervisor",
            reason="Unreviewed forensic alert in sequence range",
        )
        self.assertEqual(p_rejected.status, "rejected")

        # Future attempts to sign or submit are rejected
        with self.assertRaises(ValueError) as ctx:
            multisig_service.sign_anchor_proposal(
                self.db,
                proposal_id=proposal.id,
                signer_user_id="admin-user-2",
                signer_role="admin",
            )
        self.assertIn("rejected", str(ctx.exception).lower())

    def test_multisig_payload_tamper_invalidation(self):
        """Altering sequence range or root hash breaks signature payload digest verification."""
        proposal = multisig_service.create_anchor_proposal(
            self.db,
            site_id="site-alpha",
            from_seq=0,
            through_seq=3,
            created_by="admin-user-1",
        )
        multisig_service.sign_anchor_proposal(self.db, proposal.id, "sup-1", "supervisor")
        multisig_service.sign_anchor_proposal(self.db, proposal.id, "admin-2", "admin")

        # Simulate direct SQL tampering of merkle_root
        proposal.merkle_root = "f" * 64
        self.db.commit()

        # Submission should detect signature verification failure
        with self.assertRaises(ValueError) as ctx:
            multisig_service.submit_anchor_proposal(self.db, proposal.id, "admin-user-1")
        self.assertIn("altered proposal data", str(ctx.exception).lower())

    # =========================================================================
    # PART 4: FASTAPI ENDPOINTS
    # =========================================================================

    def test_api_endpoints_merkle_and_provenance(self):
        """Tests FastAPI endpoints for Merkle inclusion and AI provenance."""
        supervisor_payload = {"sub": "sup-1", "role": "supervisor", "site_ids": ["*"]}

        # Merkle proof endpoint
        proof = get_alert_merkle_proof(alert_id="ALT-ADV-0", db=self.db, user_payload=supervisor_payload)
        self.assertEqual(proof.alert_id, "ALT-ADV-0")
        self.assertEqual(len(proof.root_hash), 64)

        # Merkle verify endpoint
        verify_req = schemas.MerkleProofVerifyRequest(
            alert_id=proof.alert_id,
            sequence=proof.sequence,
            leaf_hash=proof.leaf_hash,
            sibling_hashes=proof.sibling_hashes,
            positions=proof.positions,
            root_hash=proof.root_hash,
        )
        v_res = verify_merkle_proof_endpoint(verify_req, user_payload=supervisor_payload)
        self.assertTrue(v_res.valid)

        # Alert provenance endpoint
        prov_res = get_alert_provenance(alert_id="ALT-ADV-0", db=self.db, user_payload=supervisor_payload)
        self.assertEqual(prov_res.alert_id, "ALT-ADV-0")
        self.assertEqual(prov_res.provenance, "detector")

        # Alert provenance verify endpoint
        v_prov = verify_alert_provenance_endpoint(alert_id="ALT-ADV-0", db=self.db, user_payload=supervisor_payload)
        self.assertTrue(v_prov.matches)

    def test_api_endpoints_proposals_workflow(self):
        """Tests end-to-end proposal workflow through FastAPI endpoints."""
        admin_payload = {"sub": "adm-1", "role": "admin", "site_ids": ["*"]}
        supervisor_payload = {"sub": "sup-1", "role": "supervisor", "site_ids": ["*"]}

        # 1. Create proposal
        req = schemas.AnchorProposalCreate(site_id="site-alpha", from_sequence=0, through_sequence=3)
        proposal = create_proposal_endpoint(req, db=self.db, user_payload=admin_payload)
        self.assertEqual(proposal.status, "proposed")

        # 2. Sign 1
        sign_req = schemas.AnchorSignRequest(reason="Forensics checked")
        p1 = sign_proposal_endpoint(proposal.id, sign_req, db=self.db, user_payload=supervisor_payload)
        self.assertEqual(p1.status, "partially_signed")

        # 3. Sign 2
        p2 = sign_proposal_endpoint(proposal.id, sign_req, db=self.db, user_payload=admin_payload)
        self.assertEqual(p2.status, "approved")

        # 4. Submit
        p3 = submit_proposal_endpoint(proposal.id, db=self.db, user_payload=admin_payload)
        self.assertIn(p3.status, ["submitted", "confirmed"])

        # 5. Verify
        v_prop = verify_proposal_endpoint(proposal.id, db=self.db, user_payload=supervisor_payload)
        self.assertTrue(v_prop.get("valid"))


if __name__ == "__main__":
    unittest.main()

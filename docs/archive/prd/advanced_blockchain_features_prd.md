# IBVAP Advanced Blockchain Integrity PRD

## Merkle Proofs, AI Model Provenance, and Multisignature Anchoring

## 1. Document Control

| Field | Value |
|---|---|
| Product | IBVAP Intelligent Border Video Analytics Platform |
| Feature | Advanced Blockchain Integrity Layer |
| Version | 1.0 |
| Status | Proposed Prototype Extension |
| Priority | High |
| Depends on | Existing local SHA-256 ledger and alert pipeline |

## 2. Executive Summary

IBVAP already maintains a local SHA-256 hash-chain for tamper detection. This PRD extends that foundation with three advanced capabilities:

1. **Merkle proofs** for efficient verification of individual alerts.
2. **AI model provenance** to prove which detector model and rule configuration generated an alert.
3. **Multisignature anchoring** so that external ledger anchoring requires approval from multiple authorized roles.

The prototype remains privacy-preserving: alert content, snapshots, GPS coordinates, face data, plate data, and credentials remain off-chain. Blockchain transactions contain only hashes, sequence metadata, model/configuration commitments, and signatures.

## 3. Problem Statement

The current local hash chain can identify database tampering, but verification requires walking the entire chain. It also does not yet provide a cryptographically verifiable record of which AI model or rule configuration generated an alert, nor does it require independent authorization before publishing an external ledger commitment.

IBVAP needs stronger integrity guarantees without introducing the operational complexity of a full multi-node blockchain deployment.

## 4. Goals

- Verify one alert using a compact Merkle inclusion proof.
- Record the exact AI model, model artifact, rule version, and configuration hashes used for an alert.
- Require multiple authorized approvals before publishing a ledger root externally.
- Preserve the current alerting and local ledger behavior when blockchain services are disabled.
- Keep all sensitive operational and personal data off-chain.
- Provide demonstrable cryptographic verification in the dashboard.

## 5. Non-Goals

- Storing alert evidence or personal data on-chain.
- Deploying Hyperledger Fabric, Besu, or another full consortium network in the initial prototype.
- Building a cryptocurrency or token economy.
- Claiming that cryptographic integrity proves an alert is factually correct.
- Replacing the local database or existing SHA-256 chain.
- Requiring a live blockchain network in automated CI.

## 6. Proposed Architecture

```text
Camera frame
   |
   v
AI detector + rule engine
   |
   +--> Encrypted evidence storage
   |
   +--> Alert record with model/config hashes
   |
   v
Local SHA-256 hash chain
   |
   v
Deterministic Merkle tree for a ledger range
   |
   v
Multisignature approval workflow
   |
   v
External blockchain anchor containing root + provenance commitment
```

## 7. Terminology

| Term | Meaning |
|---|---|
| Ledger record | Existing tamper-evident record linked to an alert |
| Merkle leaf | Hash representing one ordered ledger record |
| Merkle root | Single hash committing to a complete ledger range |
| Merkle proof | Sibling hashes proving one leaf belongs to a root |
| Model provenance | Cryptographic identity of the model and configuration used for an alert |
| Anchor | External blockchain transaction containing a root commitment |
| Signer | Authorized user or service account approving an anchor |
| Threshold | Minimum number of distinct valid signatures required |

## 8. Functional Requirements

### FR-MP-1: Merkle tree generation

1. The system shall generate a deterministic Merkle tree for a selected site and ledger sequence range.
2. Leaves shall be ordered by site ID and ledger sequence.
3. Each leaf shall include at least:
   - Site ID or site ID hash.
   - Ledger sequence.
   - Alert ID.
   - Existing ledger record hash.
   - Model provenance hash, when available.
   - Rule/configuration hash, when available.
4. Leaf and parent hashing shall use a documented algorithm, initially SHA-256.
5. The tree construction shall be deterministic across repeated runs.
6. The system shall reject empty ranges and ranges containing missing ledger records.
7. The system shall store the Merkle root and tree schema version with the anchor request.

Recommended leaf payload:

```json
{
  "schemaVersion": "merkle-v1",
  "siteId": "site-alpha",
  "sequence": 42,
  "alertId": "EVT-0042",
  "ledgerRecordHash": "...",
  "modelProvenanceHash": "...",
  "ruleConfigHash": "..."
}
```

### FR-MP-2: Individual Merkle proofs

1. The system shall generate an inclusion proof for an alert ID and ledger sequence.
2. A proof shall contain:
   - Leaf hash.
   - Leaf payload or a privacy-safe leaf reference.
   - Sibling hashes.
   - Left/right position for each sibling.
   - Root hash.
   - Tree schema version.
   - Sequence range.
3. The system shall verify a proof without reading every alert in the range.
4. A modified leaf, sibling, root, or sequence shall cause verification to fail.
5. Proof verification shall return the first detected mismatch where determinable.

### FR-MP-3: Merkle APIs

#### `POST /ledger/merkle/build`

Role: Supervisor or Admin.

```json
{
  "siteId": "site-alpha",
  "fromSequence": 1,
  "throughSequence": 100
}
```

Response:

```json
{
  "rootHash": "...",
  "leafCount": 100,
  "fromSequence": 1,
  "throughSequence": 100,
  "schemaVersion": "merkle-v1"
}
```

#### `GET /ledger/proof/{alertId}`

Role: Supervisor or Admin.

Returns the compact inclusion proof for the alert.

#### `POST /ledger/proof/verify`

Role: Supervisor or Admin.

Accepts a proof and returns:

```json
{
  "valid": true,
  "alertId": "EVT-0042",
  "rootHash": "...",
  "message": "Alert is included in the requested Merkle root."
}
```

### FR-MP-4: Model provenance

Every detector-generated alert shall record the provenance of the inference that produced it.

Required provenance fields:

- Detector model name.
- Detector model version.
- Model artifact SHA-256 hash.
- Inference runtime or framework version.
- Rule engine version.
- Fence/rule configuration hash.
- Preprocessing configuration hash where applicable.
- Detector timestamp.
- Camera ID.
- Site ID.

Recommended alert fields:

```text
model_name
model_version
model_artifact_hash
runtime_version
rule_version
rule_config_hash
preprocessing_config_hash
provenance_hash
```

The combined provenance hash shall be calculated from a canonical, sorted JSON object:

```json
{
  "modelName": "yolov8n",
  "modelVersion": "8.2.0",
  "modelArtifactHash": "...",
  "runtimeVersion": "...",
  "ruleVersion": "1.0",
  "ruleConfigHash": "...",
  "preprocessingConfigHash": "..."
}
```

Requirements:

1. The same model and configuration produce the same provenance hash.
2. Changing any provenance field changes the hash.
3. Missing provenance must be represented as unavailable, not fabricated.
4. Simulation alerts must use explicit simulation provenance and must not claim detector provenance.
5. The model artifact hash shall be calculated from the deployed artifact or a registered immutable artifact reference.
6. Existing alerts may have nullable provenance fields for backward compatibility.

### FR-MP-5: Provenance APIs

#### `GET /models/{modelVersion}/provenance`

Returns registered model metadata and artifact hash.

#### `GET /alerts/{alertId}/provenance`

Returns the model, rule, configuration, and combined provenance hash associated with an alert.

#### `POST /alerts/{alertId}/provenance/verify`

Recomputes and verifies the alert provenance hash against the stored value.

### FR-MS-1: Multisignature anchor policy

1. An external ledger anchor shall require a configurable approval threshold.
2. Signers must be authenticated IBVAP users with authorized roles.
3. A signer may not approve the same request twice.
4. The same user cannot satisfy multiple threshold slots.
5. Each signature shall cover the exact anchor payload:
   - Anchor request ID.
   - Site ID or site hash.
   - Ledger sequence range.
   - Merkle root.
   - Model provenance commitment root, if included.
   - Chain/network identifier.
   - Expiry timestamp.
6. Any change to the payload invalidates existing signatures.
7. The anchor must not be submitted until the threshold is met.
8. The default prototype policy shall be 2-of-3 for Admin and Supervisor signers.

### FR-MS-2: Signature methods

The prototype may use application-level signatures backed by registered signing keys. Preferred production-compatible options:

- Ed25519 signatures stored as public-key credentials.
- WebAuthn/FIDO2 signatures for human approvals.
- Hardware-backed keys for field deployment.

Passwords or JWTs must not be used as signatures.

### FR-MS-3: Multisignature workflow

Statuses:

```text
proposed
partially_signed
approved
submitted
confirmed
rejected
expired
failed
```

Workflow:

```text
Create anchor proposal
        ↓
Calculate Merkle root and provenance commitment
        ↓
Collect distinct authorized signatures
        ↓
Reach threshold
        ↓
Submit blockchain transaction
        ↓
Track confirmations
        ↓
Verify local root against on-chain commitment
```

Requirements:

- Admin creates or submits the proposal.
- Supervisor/Admin signs according to policy.
- The UI displays signer identities, roles, timestamps, and signature status.
- A signer can reject a proposal with a required reason.
- Proposals expire after a configurable period.
- Any failed signature or transaction is auditable.

### FR-MS-4: Anchor payload

The external blockchain transaction shall include only:

```json
{
  "anchorId": "ANCH-0001",
  "siteIdHash": "...",
  "fromSequence": 1,
  "throughSequence": 100,
  "merkleRoot": "...",
  "provenanceRoot": "...",
  "schemaVersion": "ibvap-anchor-v1"
}
```

No alert detail, snapshot, location, face data, plate data, credential, or encryption key may be included.

## 9. Data Model

### `MerkleAnchor`

```text
id
site_id
from_sequence
through_sequence
merkle_root
provenance_root
schema_version
status
network
chain_id
contract_address
transaction_hash
block_number
created_by
created_at
submitted_at
confirmed_at
expires_at
last_error
```

### `AnchorSignature`

```text
id
anchor_id
signer_user_id
signer_role
signature_algorithm
public_key_id
signature
payload_digest
status
reason
signed_at
expires_at
```

### `ModelProvenance`

```text
id
model_name
model_version
artifact_hash
runtime_version
rule_version
rule_config_hash
preprocessing_config_hash
provenance_hash
registered_by
created_at
```

Add uniqueness constraints for:

- Anchor ID.
- `(site_id, from_sequence, through_sequence, merkle_root)`.
- `(anchor_id, signer_user_id)`.
- Model name and version where appropriate.

## 10. Smart Contract Requirements

The contract shall:

- Accept a Merkle root and optional provenance root.
- Store the anchor ID, site hash, sequence range, roots, and schema version.
- Emit an `AnchorCommitted` event.
- Reject duplicate anchor IDs.
- Restrict writes to the authorized anchoring account or approved relayer.
- Support read-back by anchor ID.

Example event:

```solidity
event AnchorCommitted(
    bytes32 indexed anchorId,
    bytes32 indexed siteIdHash,
    uint64 fromSequence,
    uint64 throughSequence,
    bytes32 merkleRoot,
    bytes32 provenanceRoot,
    uint8 schemaVersion,
    uint256 timestamp
);
```

Application-level multisignature approval shall happen before the transaction is submitted. A later production version may move threshold enforcement into the contract using a multisignature wallet.

## 11. Backend API Surface

### `POST /ledger/anchors/proposals`

Admin only. Creates a proposal and calculates the Merkle/provenance commitments.

### `GET /ledger/anchors/proposals`

Supervisor/Admin. Lists proposals by site, status, and date.

### `GET /ledger/anchors/proposals/{id}`

Supervisor/Admin. Returns proposal payload and signature status.

### `POST /ledger/anchors/proposals/{id}/sign`

Supervisor/Admin. Adds one authenticated cryptographic signature.

### `POST /ledger/anchors/proposals/{id}/reject`

Supervisor/Admin. Rejects the proposal with a reason.

### `POST /ledger/anchors/proposals/{id}/submit`

Admin only. Submits only when the configured threshold is satisfied.

### `POST /ledger/anchors/{id}/verify`

Supervisor/Admin. Verifies local chain, Merkle root, provenance root, and external transaction.

### `GET /alerts/{alertId}/merkle-proof`

Supervisor/Admin. Returns an individual proof.

### `GET /alerts/{alertId}/provenance`

Supervisor/Admin. Returns model and rule provenance.

Existing `GET /ledger/verify` must continue to work and must not require blockchain availability.

## 12. Frontend Requirements

Add an Integrity and Provenance section to the existing Alerts Log or ledger verification surface.

### Merkle proof UI

- `Generate Proof` action for an alert.
- Proof validity state.
- Root hash.
- Sequence range.
- Leaf sequence.
- Copy/export proof action.
- Clear mismatch state.

### Model provenance UI

Display:

- Model name/version.
- Artifact hash.
- Runtime version.
- Rule version.
- Rule/config hash.
- Provenance verification status.
- Simulation or detector provenance.

### Multisignature UI

Display:

- Proposal status.
- Required signatures, such as `2 of 3`.
- Signer names and roles.
- Signature timestamps.
- Approve, reject, submit, and verify actions based on RBAC.
- Pending, expired, failed, confirmed, and mismatch states.

Rules:

- Operator: view proof and provenance only.
- Supervisor: view, verify, and sign where policy allows.
- Admin: create, submit, retry, and manage proposals.

## 13. Configuration

```text
IBVAP_ADVANCED_INTEGRITY_ENABLED=false
IBVAP_MERKLE_SCHEMA_VERSION=merkle-v1
IBVAP_ANCHOR_SCHEMA_VERSION=ibvap-anchor-v1
IBVAP_ANCHOR_SIGNATURE_THRESHOLD=2
IBVAP_ANCHOR_SIGNATURE_ROLES=admin,supervisor
IBVAP_ANCHOR_EXPIRY_SECONDS=86400
IBVAP_BLOCKCHAIN_NETWORK=sepolia
IBVAP_BLOCKCHAIN_CHAIN_ID=11155111
IBVAP_BLOCKCHAIN_RPC_URL=
IBVAP_BLOCKCHAIN_CONTRACT_ADDRESS=
IBVAP_BLOCKCHAIN_PRIVATE_KEY=
```

Rules:

- Disabled mode must not affect alert creation or local ledger verification.
- Secrets must be supplied through environment variables or a secrets manager.
- Private keys must never be committed, logged, or returned through APIs.
- CI must use a mocked blockchain provider.

## 14. Security and Privacy Requirements

- Use canonical serialization before hashing or signing.
- Include domain separation in signed payloads to prevent replay across environments.
- Include an expiry timestamp and network identifier in every signature payload.
- Validate signer role and public key before accepting a signature.
- Reject duplicate signatures from the same identity.
- Protect signing keys with WebAuthn, HSM, or equivalent hardware-backed storage in production.
- Encrypt stored signatures and sensitive key references at rest.
- Do not expose private keys through error messages, logs, backups, or frontend responses.
- Do not store raw evidence or identifying data on-chain.
- Audit every proposal, signature, rejection, submission, retry, and verification.

## 15. Testing Requirements

### Merkle tests

- Repeated input produces the same root.
- Changing one ledger record changes the root.
- Reordering leaves changes the root.
- Single-alert inclusion proof verifies successfully.
- Modified leaf fails verification.
- Modified sibling fails verification.
- Wrong root fails verification.
- Empty and incomplete ranges are rejected.

### Provenance tests

- Identical model/configuration produces an identical provenance hash.
- Changing model version changes the hash.
- Changing artifact hash changes the hash.
- Changing rule configuration changes the hash.
- Missing metadata remains unavailable.
- Simulation alerts do not claim detector provenance.

### Multisignature tests

- One signature does not satisfy a 2-of-3 policy.
- Two distinct authorized signatures satisfy the policy.
- Duplicate signer signatures are rejected.
- Unauthorized roles cannot sign.
- Payload changes invalidate signatures.
- Expired proposals cannot be submitted.
- Rejected proposals cannot be submitted.
- Blockchain submission is blocked until threshold approval.

### Integration tests

1. Create alerts through the existing pipeline.
2. Append them to the local hash chain.
3. Register model and rule provenance.
4. Generate the Merkle root and provenance root.
5. Create an anchor proposal.
6. Collect two authorized signatures.
7. Submit through a mocked blockchain provider.
8. Verify the transaction and individual alert proof.
9. Modify an alert locally.
10. Confirm local chain, Merkle proof, and provenance verification fail appropriately.

## 16. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Availability | Alerting and local ledger operation continue when advanced blockchain features are disabled or unavailable. |
| Privacy | No sensitive surveillance data is written on-chain. |
| Integrity | Roots and proofs are deterministic and reproducible. |
| Security | Threshold signatures, expiry, domain separation, and role validation are enforced. |
| Performance | Individual proof verification does not require scanning the complete ledger. |
| Auditability | All proposal and signature actions are recorded in the audit log. |
| Operability | Administrators can diagnose pending, failed, rejected, and mismatched states. |
| Testability | CI works without a live blockchain wallet or network. |

## 17. Acceptance Criteria

The feature is complete when:

1. An alert can be verified with an individual Merkle proof.
2. A changed alert fails Merkle verification.
3. An alert exposes the model artifact, rule, runtime, and combined provenance hash used to create it.
4. Changing any provenance input changes the provenance hash.
5. A 2-of-3 multisignature policy blocks submission after one signature.
6. Two distinct authorized signatures permit submission.
7. Duplicate and unauthorized signatures are rejected.
8. Signature payload changes invalidate previous approvals.
9. The external anchor contains only hashes and sequence metadata.
10. Blockchain or RPC failure does not block local alert creation or local ledger verification.
11. The UI clearly shows proof validity, provenance status, signer threshold, and anchor state.
12. Existing full PRD tests remain green.
13. All new unit, API, and integration tests pass with a mocked blockchain provider.
14. The application starts and works normally with `IBVAP_ADVANCED_INTEGRITY_ENABLED=false`.

## 18. Delivery Plan

### Phase 1: Cryptographic foundations

- Add canonical provenance hashing.
- Add Merkle tree and proof generation.
- Add proof verification APIs and tests.

### Phase 2: Provenance integration

- Add model registry artifact hashes.
- Attach model and rule provenance to new alerts.
- Add provenance verification UI.

### Phase 3: Multisignature workflow

- Add proposal and signature models.
- Add role-aware signing and rejection.
- Add threshold validation and audit events.

### Phase 4: External anchor

- Add mocked blockchain provider.
- Add minimal smart contract.
- Add testnet submission and confirmation tracking.
- Add external anchor verification.

## 19. Honest Product Claim

IBVAP may claim:

> IBVAP provides independently verifiable integrity proofs for surveillance alert records, including Merkle inclusion proofs, AI model provenance, and threshold-authorized external ledger anchoring.

IBVAP must not claim that blockchain proves an alert is factually true. It proves that the recorded alert, its declared provenance, and its ledger position have not changed since the commitment was created and anchored.

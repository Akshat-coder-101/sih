import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

// 1. Client-Side Cryptographic Merkle Verification Simulation (FR-MP-2)
function computeMerkleRootFromProof(leafHash, siblingHashes, positions) {
  let current = leafHash;
  for (let i = 0; i < siblingHashes.length; i++) {
    const sibling = siblingHashes[i];
    const pos = positions[i];
    const hasher = crypto.createHash('sha256');
    if (pos === 'left') {
      hasher.update(sibling + current);
    } else {
      hasher.update(current + sibling);
    }
    current = hasher.digest('hex');
  }
  return current;
}

// 2. Multisig State Machine & RBAC Matrix (FR-MS-1 to FR-MS-4)
function evaluateProposalState(signatures, thresholdRequired = 2) {
  const distinctValidSigners = new Set(
    signatures.filter(s => s.status === 'signed').map(s => s.signerUserId)
  );

  const hasRejection = signatures.some(s => s.status === 'rejected');
  if (hasRejection) return 'rejected';

  if (distinctValidSigners.size >= thresholdRequired) {
    return 'approved';
  } else if (distinctValidSigners.size > 0) {
    return 'partially_signed';
  }
  return 'proposed';
}

function canPerformMultisigAction(role, action, proposalStatus = 'proposed') {
  if (action === 'create_proposal') {
    return role === 'admin';
  }
  if (action === 'sign_proposal' || action === 'reject_proposal') {
    return (role === 'supervisor' || role === 'admin') && (proposalStatus === 'proposed' || proposalStatus === 'partially_signed');
  }
  if (action === 'submit_proposal') {
    return role === 'admin' && proposalStatus === 'approved';
  }
  if (action === 'view_proposals' || action === 'inspect_proof' || action === 'inspect_provenance') {
    return true; // All authenticated roles can inspect forensic integrity
  }
  return false;
}

// 3. AI Model Provenance Discrimination (FR-MP-4.4)
function validateAlertProvenanceMetadata(prov) {
  if (prov.provenance === 'simulation') {
    assert.equal(prov.modelName, 'Synthetic-Simulation-Engine');
    assert.equal(prov.modelArtifactHash, 'sim-synthetic-artifact-no-detector-weights');
    return { isSimulated: true, weightsClaimed: false };
  } else if (prov.provenance === 'detector') {
    assert.notEqual(prov.modelArtifactHash, 'sim-synthetic-artifact-no-detector-weights');
    assert.ok(prov.modelArtifactHash && prov.modelArtifactHash.length === 64);
    return { isSimulated: false, weightsClaimed: true };
  }
  throw new Error(`Unknown provenance type: ${prov.provenance}`);
}

// Test Suites
test('1. Merkle Proof: verifies inclusion mathematically along sibling path', () => {
  // Let leaf be H(leaf_payload)
  const leafHash = crypto.createHash('sha256').update('leaf_data_alert_101').digest('hex');
  const sibling1 = crypto.createHash('sha256').update('leaf_data_alert_102').digest('hex');
  
  // Sibling1 is to the right
  const parent1 = crypto.createHash('sha256').update(leafHash + sibling1).digest('hex');
  
  // Sibling2 is to the left
  const sibling2 = crypto.createHash('sha256').update('subtree_left').digest('hex');
  const expectedRoot = crypto.createHash('sha256').update(sibling2 + parent1).digest('hex');

  const computed = computeMerkleRootFromProof(leafHash, [sibling1, sibling2], ['right', 'left']);
  assert.equal(computed, expectedRoot);
});

test('2. Merkle Proof: detects tampering in leaf or sibling hash', () => {
  const leafHash = crypto.createHash('sha256').update('leaf_data_alert_101').digest('hex');
  const tamperedLeaf = crypto.createHash('sha256').update('tampered_leaf_alert_101').digest('hex');
  const sibling1 = crypto.createHash('sha256').update('sibling_1').digest('hex');

  const validRoot = crypto.createHash('sha256').update(leafHash + sibling1).digest('hex');
  const tamperedRoot = computeMerkleRootFromProof(tamperedLeaf, [sibling1], ['right']);

  assert.notEqual(tamperedRoot, validRoot, 'Tampered leaf must yield a different Merkle root');
});

test('3. AI Model Provenance: strictly discriminates simulation from detector models', () => {
  const detectorProv = {
    alertId: 'alt-det-01',
    provenance: 'detector',
    modelName: 'yolov8n-ibvap-v1.0',
    modelArtifactHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
  };
  const detResult = validateAlertProvenanceMetadata(detectorProv);
  assert.equal(detResult.isSimulated, false);
  assert.equal(detResult.weightsClaimed, true);

  const simProv = {
    alertId: 'alt-sim-02',
    provenance: 'simulation',
    modelName: 'Synthetic-Simulation-Engine',
    modelArtifactHash: 'sim-synthetic-artifact-no-detector-weights',
  };
  const simResult = validateAlertProvenanceMetadata(simProv);
  assert.equal(simResult.isSimulated, true);
  assert.equal(simResult.weightsClaimed, false);
});

test('4. Multisig Proposals: 2-of-3 threshold state transitions', () => {
  // Empty signatures -> proposed
  assert.equal(evaluateProposalState([], 2), 'proposed');

  // 1 signature -> partially_signed
  const sig1 = [{ signerUserId: 'user-sup-1', status: 'signed' }];
  assert.equal(evaluateProposalState(sig1, 2), 'partially_signed');

  // Duplicate signature from same user does not satisfy 2-of-3
  const dupSigs = [
    { signerUserId: 'user-sup-1', status: 'signed' },
    { signerUserId: 'user-sup-1', status: 'signed' },
  ];
  assert.equal(evaluateProposalState(dupSigs, 2), 'partially_signed');

  // 2 distinct signatures -> approved
  const approvedSigs = [
    { signerUserId: 'user-sup-1', status: 'signed' },
    { signerUserId: 'user-adm-2', status: 'signed' },
  ];
  assert.equal(evaluateProposalState(approvedSigs, 2), 'approved');

  // Rejection by any participant -> rejected
  const rejectedSigs = [
    { signerUserId: 'user-sup-1', status: 'signed' },
    { signerUserId: 'user-adm-2', status: 'rejected', reason: 'Forensic hold' },
  ];
  assert.equal(evaluateProposalState(rejectedSigs, 2), 'rejected');
});

test('5. Multisig RBAC Matrix: enforcement across Operator, Supervisor, and Admin', () => {
  // Operators cannot create, sign, or submit proposals
  assert.equal(canPerformMultisigAction('operator', 'create_proposal'), false);
  assert.equal(canPerformMultisigAction('operator', 'sign_proposal'), false);
  assert.equal(canPerformMultisigAction('operator', 'submit_proposal'), false);
  assert.equal(canPerformMultisigAction('operator', 'inspect_proof'), true);

  // Supervisors can sign and reject, but cannot create or submit to chain
  assert.equal(canPerformMultisigAction('supervisor', 'create_proposal'), false);
  assert.equal(canPerformMultisigAction('supervisor', 'sign_proposal', 'proposed'), true);
  assert.equal(canPerformMultisigAction('supervisor', 'reject_proposal', 'partially_signed'), true);
  assert.equal(canPerformMultisigAction('supervisor', 'submit_proposal', 'approved'), false);

  // Admins can create, sign, and submit when approved
  assert.equal(canPerformMultisigAction('admin', 'create_proposal'), true);
  assert.equal(canPerformMultisigAction('admin', 'sign_proposal', 'partially_signed'), true);
  assert.equal(canPerformMultisigAction('admin', 'submit_proposal', 'partially_signed'), false);
  assert.equal(canPerformMultisigAction('admin', 'submit_proposal', 'approved'), true);
});

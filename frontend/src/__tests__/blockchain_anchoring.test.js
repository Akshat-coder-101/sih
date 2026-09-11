import test from 'node:test';
import assert from 'node:assert/strict';

// Helper functions that match frontend Blockchain Anchoring logic
function getAnchorStatusBadge(status) {
  switch (status) {
    case 'confirmed':
      return { label: 'Confirmed On-Chain', tone: 'leaf', icon: 'ti-circle-check' };
    case 'submitted':
      return { label: 'Submitted (Awaiting Blocks)', tone: 'cyan', icon: 'ti-clock' };
    case 'pending':
      return { label: 'Pending Submission', tone: 'amber', icon: 'ti-loader' };
    case 'failed':
      return { label: 'Submission Failed', tone: 'melon', icon: 'ti-alert-triangle' };
    case 'verification_failed':
      return { label: 'Verification Failed', tone: 'melon', icon: 'ti-shield-alert' };
    default:
      return { label: 'Not Configured', tone: 'slate', icon: 'ti-info-circle' };
  }
}

function truncateRootHash(hash, length = 16) {
  if (!hash) return '';
  if (hash.length <= length) return hash;
  return `${hash.slice(0, length)}...`;
}

function canPerformBlockchainAction(role, action) {
  if (action === 'view_local_ledger') return true;
  if (action === 'verify_anchor' || action === 'list_anchors') {
    return role === 'supervisor' || role === 'admin';
  }
  if (action === 'create_anchor' || action === 'retry_anchor') {
    return role === 'admin';
  }
  return false;
}

function normalizeLedgerVerifyResponse(raw) {
  return {
    intact: Boolean(raw.intact),
    checkedRecords: Number(raw.checkedRecords ?? raw.checked_records ?? 0),
    blockchainAnchorsAvailable: Boolean(raw.blockchainAnchorsAvailable ?? raw.blockchain_anchors_available ?? false),
    latestAnchorId: raw.latestAnchorId ?? raw.latest_anchor_id ?? null,
    latestAnchorStatus: raw.latestAnchorStatus ?? raw.latest_anchor_status ?? null,
    latestAnchorMatches: raw.latestAnchorMatches ?? raw.latest_anchor_matches ?? null,
  };
}

test('1. Status badge mapping accurately reflects on-chain states (FR-BA-4)', () => {
  const confirmed = getAnchorStatusBadge('confirmed');
  assert.equal(confirmed.label, 'Confirmed On-Chain');
  assert.equal(confirmed.tone, 'leaf');

  const submitted = getAnchorStatusBadge('submitted');
  assert.equal(submitted.label, 'Submitted (Awaiting Blocks)');
  assert.equal(submitted.tone, 'cyan');

  const failed = getAnchorStatusBadge('failed');
  assert.equal(failed.label, 'Submission Failed');
  assert.equal(failed.tone, 'melon');

  const verFailed = getAnchorStatusBadge('verification_failed');
  assert.equal(verFailed.label, 'Verification Failed');
  assert.equal(verFailed.tone, 'melon');

  const fallback = getAnchorStatusBadge('unknown');
  assert.equal(fallback.label, 'Not Configured');
});

test('2. Root hash formatting and truncation for UI display', () => {
  const sampleHash = '3a7bd3e2360a3d29eea436fcfb7e44c735d117c42d1c1835420b6b9942dd4f1b';
  assert.equal(sampleHash.length, 64);
  const truncated = truncateRootHash(sampleHash, 16);
  assert.equal(truncated, '3a7bd3e2360a3d29...');
  assert.equal(truncateRootHash(''), '');
});

test('3. Role-Based Access Control matrix for blockchain actions (FR-BA-2, FR-BA-5, Section 12)', () => {
  // Operator: view local ledger only
  assert.equal(canPerformBlockchainAction('operator', 'view_local_ledger'), true);
  assert.equal(canPerformBlockchainAction('operator', 'verify_anchor'), false);
  assert.equal(canPerformBlockchainAction('operator', 'create_anchor'), false);
  assert.equal(canPerformBlockchainAction('operator', 'retry_anchor'), false);

  // Supervisor: view and verify anchors
  assert.equal(canPerformBlockchainAction('supervisor', 'view_local_ledger'), true);
  assert.equal(canPerformBlockchainAction('supervisor', 'verify_anchor'), true);
  assert.equal(canPerformBlockchainAction('supervisor', 'create_anchor'), false);
  assert.equal(canPerformBlockchainAction('supervisor', 'retry_anchor'), false);

  // Admin: full authority to create, retry, and verify anchors
  assert.equal(canPerformBlockchainAction('admin', 'view_local_ledger'), true);
  assert.equal(canPerformBlockchainAction('admin', 'verify_anchor'), true);
  assert.equal(canPerformBlockchainAction('admin', 'create_anchor'), true);
  assert.equal(canPerformBlockchainAction('admin', 'retry_anchor'), true);
});

test('4. Ledger verify response parser supports both camelCase and snake_case backend responses', () => {
  const parsedCamel = normalizeLedgerVerifyResponse({
    intact: true,
    checkedRecords: 42,
    blockchainAnchorsAvailable: true,
    latestAnchorId: 'ANCH-0001',
    latestAnchorStatus: 'confirmed',
    latestAnchorMatches: true,
  });
  assert.equal(parsedCamel.intact, true);
  assert.equal(parsedCamel.checkedRecords, 42);
  assert.equal(parsedCamel.blockchainAnchorsAvailable, true);
  assert.equal(parsedCamel.latestAnchorId, 'ANCH-0001');
  assert.equal(parsedCamel.latestAnchorMatches, true);

  const parsedSnake = normalizeLedgerVerifyResponse({
    intact: true,
    checked_records: 10,
    blockchain_anchors_available: true,
    latest_anchor_id: 'ANCH-0002',
    latest_anchor_status: 'submitted',
    latest_anchor_matches: false,
  });
  assert.equal(parsedSnake.checkedRecords, 10);
  assert.equal(parsedSnake.latestAnchorId, 'ANCH-0002');
  assert.equal(parsedSnake.latestAnchorStatus, 'submitted');
  assert.equal(parsedSnake.latestAnchorMatches, false);
});

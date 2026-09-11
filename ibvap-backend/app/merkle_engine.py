import hashlib
import json
from typing import List, Dict, Any, Tuple, Optional


def canonical_json(data: Any) -> str:
    """Deterministic, sorted, whitespace-minimized canonical JSON string."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def build_canonical_leaf_payload(
    site_id: str,
    sequence: int,
    alert_id: str,
    record_hash: str,
    model_provenance_hash: Optional[str] = None,
    rule_config_hash: Optional[str] = None,
    schema_version: str = "merkle-v1",
) -> Dict[str, Any]:
    """Canonical Merkle leaf dictionary matching PRD FR-MP-1."""
    return {
        "schemaVersion": schema_version,
        "siteId": site_id,
        "sequence": sequence,
        "alertId": alert_id,
        "ledgerRecordHash": record_hash,
        "modelProvenanceHash": model_provenance_hash or "none",
        "ruleConfigHash": rule_config_hash or "none",
    }


def compute_leaf_hash(payload: Dict[str, Any]) -> str:
    """Deterministic SHA-256 digest of canonical leaf payload."""
    canonical_bytes = canonical_json(payload).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def hash_pair(left: str, right: str) -> str:
    """Pairwise parent hash: sha256(left:right)."""
    return hashlib.sha256(f"{left}:{right}".encode("utf-8")).hexdigest()


def build_merkle_tree(leaf_hashes: List[str]) -> Tuple[str, List[List[str]]]:
    """
    Constructs a full deterministic Merkle tree from leaf hashes.
    Duplicates the odd leaf on unbalanced levels.
    Returns (root_hash, levels) where levels[0] is leaves and levels[-1][0] is the root.
    """
    if not leaf_hashes:
        raise ValueError("Cannot construct Merkle tree from empty leaf list")

    levels: List[List[str]] = [list(leaf_hashes)]
    current = list(leaf_hashes)

    while len(current) > 1:
        next_level: List[str] = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else left
            parent = hash_pair(left, right)
            next_level.append(parent)
        levels.append(next_level)
        current = next_level

    return current[0], levels


def generate_merkle_proof(leaf_hashes: List[str], target_index: int) -> Tuple[List[str], List[str]]:
    """
    Generates an inclusion proof for leaf at `target_index`.
    Returns (sibling_hashes, positions) where each position is 'left' or 'right'.
    'left' means the sibling is on the left (hash_pair(sibling, current))
    'right' means the sibling is on the right (hash_pair(current, sibling))
    """
    if target_index < 0 or target_index >= len(leaf_hashes):
        raise IndexError(f"Target index {target_index} out of bounds for {len(leaf_hashes)} leaves")

    _, levels = build_merkle_tree(leaf_hashes)
    sibling_hashes: List[str] = []
    positions: List[str] = []

    idx = target_index
    # Iterate through all levels except the root level (which has len 1)
    for level in levels[:-1]:
        is_right = (idx % 2 == 1)
        if is_right:
            # Current node is on the right; sibling is on the left
            sibling_idx = idx - 1
            sibling_hashes.append(level[sibling_idx])
            positions.append("left")
        else:
            # Current node is on the left; sibling is on the right
            sibling_idx = idx + 1 if idx + 1 < len(level) else idx
            sibling_hashes.append(level[sibling_idx])
            positions.append("right")

        idx = idx // 2

    return sibling_hashes, positions


def verify_merkle_proof(
    leaf_hash: str,
    sibling_hashes: List[str],
    positions: List[str],
    root_hash: str,
) -> Tuple[bool, str]:
    """
    Verifies a compact Merkle inclusion proof without scanning the entire tree.
    Returns (valid: bool, calculated_root: str).
    """
    if len(sibling_hashes) != len(positions):
        return False, ""

    current = leaf_hash
    for sibling, pos in zip(sibling_hashes, positions):
        if pos == "left":
            current = hash_pair(sibling, current)
        elif pos == "right":
            current = hash_pair(current, sibling)
        else:
            return False, ""

    return (current.lower() == root_hash.lower()), current


def compute_provenance_root(provenance_hashes: List[str]) -> str:
    """Computes a deterministic Merkle root over a sequence of provenance hashes."""
    if not provenance_hashes:
        return "0" * 64
    root, _ = build_merkle_tree(provenance_hashes)
    return root

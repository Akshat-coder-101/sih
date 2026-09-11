// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ILedgerAnchor
 * @notice Interface for external blockchain anchoring of the IBVAP tamper-evident ledger.
 * @dev Stores minimal cryptographic commitments (site ID hash, sequence range, Merkle root hash, AI provenance root).
 *      No surveillance data, coordinates, face embeddings, or evidence are ever stored on-chain.
 */
interface ILedgerAnchor {
    event LedgerAnchored(
        bytes32 indexed siteIdHash,
        uint64 fromSequence,
        uint64 throughSequence,
        bytes32 rootHash,
        uint8 schemaVersion,
        uint256 anchoredAt
    );

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

    function anchorLedger(
        bytes32 anchorId,
        bytes32 siteIdHash,
        uint64 fromSequence,
        uint64 throughSequence,
        bytes32 rootHash,
        uint8 schemaVersion
    ) external;

    function anchorLedgerWithProvenance(
        bytes32 anchorId,
        bytes32 siteIdHash,
        uint64 fromSequence,
        uint64 throughSequence,
        bytes32 merkleRoot,
        bytes32 provenanceRoot,
        uint8 schemaVersion
    ) external;

    function getAnchor(bytes32 anchorId)
        external
        view
        returns (
            bytes32 siteIdHash,
            uint64 fromSequence,
            uint64 throughSequence,
            bytes32 rootHash,
            uint8 schemaVersion,
            uint256 anchoredAt
        );

    function getAnchorWithProvenance(bytes32 anchorId)
        external
        view
        returns (
            bytes32 siteIdHash,
            uint64 fromSequence,
            uint64 throughSequence,
            bytes32 merkleRoot,
            bytes32 provenanceRoot,
            uint8 schemaVersion,
            uint256 timestamp
        );
}

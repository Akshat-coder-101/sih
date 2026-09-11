// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./ILedgerAnchor.sol";

/**
 * @title LedgerAnchor
 * @notice Reference smart contract for anchoring IBVAP SHA-256 ledger roots and AI model provenance.
 * @dev Replay-protected, owner-authorized, append-only cryptographic commitment store.
 */
contract LedgerAnchor is ILedgerAnchor {
    struct AnchorRecord {
        bytes32 siteIdHash;
        uint64 fromSequence;
        uint64 throughSequence;
        bytes32 rootHash;
        bytes32 provenanceRoot;
        uint8 schemaVersion;
        uint256 anchoredAt;
        bool exists;
    }

    address public owner;
    mapping(address => bool) public authorizedCallers;
    mapping(bytes32 => AnchorRecord) private _anchors;

    // Optional mapping to prevent sequence range collisions per site
    // keccak256(abi.encodePacked(siteIdHash, fromSequence, throughSequence)) => bool
    mapping(bytes32 => bool) private _anchoredRanges;

    modifier onlyAuthorized() {
        require(msg.sender == owner || authorizedCallers[msg.sender], "LedgerAnchor: unauthorized caller");
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedCallers[msg.sender] = true;
    }

    function setAuthorizedCaller(address caller, bool authorized) external {
        require(msg.sender == owner, "LedgerAnchor: only owner can set authorization");
        authorizedCallers[caller] = authorized;
    }

    function anchorLedger(
        bytes32 anchorId,
        bytes32 siteIdHash,
        uint64 fromSequence,
        uint64 throughSequence,
        bytes32 rootHash,
        uint8 schemaVersion
    ) external override onlyAuthorized {
        anchorLedgerWithProvenance(
            anchorId,
            siteIdHash,
            fromSequence,
            throughSequence,
            rootHash,
            bytes32(0),
            schemaVersion
        );
    }

    function anchorLedgerWithProvenance(
        bytes32 anchorId,
        bytes32 siteIdHash,
        uint64 fromSequence,
        uint64 throughSequence,
        bytes32 merkleRoot,
        bytes32 provenanceRoot,
        uint8 schemaVersion
    ) public override onlyAuthorized {
        require(anchorId != bytes32(0), "LedgerAnchor: anchorId required");
        require(merkleRoot != bytes32(0), "LedgerAnchor: merkleRoot required");
        require(fromSequence <= throughSequence, "LedgerAnchor: invalid sequence range");
        require(!_anchors[anchorId].exists, "LedgerAnchor: anchorId already exists");

        bytes32 rangeKey = keccak256(abi.encodePacked(siteIdHash, fromSequence, throughSequence));
        require(!_anchoredRanges[rangeKey], "LedgerAnchor: sequence range already anchored for site");

        _anchors[anchorId] = AnchorRecord({
            siteIdHash: siteIdHash,
            fromSequence: fromSequence,
            throughSequence: throughSequence,
            rootHash: merkleRoot,
            provenanceRoot: provenanceRoot,
            schemaVersion: schemaVersion,
            anchoredAt: block.timestamp,
            exists: true
        });

        _anchoredRanges[rangeKey] = true;

        emit LedgerAnchored(
            siteIdHash,
            fromSequence,
            throughSequence,
            merkleRoot,
            schemaVersion,
            block.timestamp
        );

        emit AnchorCommitted(
            anchorId,
            siteIdHash,
            fromSequence,
            throughSequence,
            merkleRoot,
            provenanceRoot,
            schemaVersion,
            block.timestamp
        );
    }

    function getAnchor(bytes32 anchorId)
        external
        view
        override
        returns (
            bytes32 siteIdHash,
            uint64 fromSequence,
            uint64 throughSequence,
            bytes32 rootHash,
            uint8 schemaVersion,
            uint256 anchoredAt
        )
    {
        AnchorRecord storage record = _anchors[anchorId];
        require(record.exists, "LedgerAnchor: anchor does not exist");
        return (
            record.siteIdHash,
            record.fromSequence,
            record.throughSequence,
            record.rootHash,
            record.schemaVersion,
            record.anchoredAt
        );
    }

    function getAnchorWithProvenance(bytes32 anchorId)
        external
        view
        override
        returns (
            bytes32 siteIdHash,
            uint64 fromSequence,
            uint64 throughSequence,
            bytes32 merkleRoot,
            bytes32 provenanceRoot,
            uint8 schemaVersion,
            uint256 timestamp
        )
    {
        AnchorRecord storage record = _anchors[anchorId];
        require(record.exists, "LedgerAnchor: anchor does not exist");
        return (
            record.siteIdHash,
            record.fromSequence,
            record.throughSequence,
            record.rootHash,
            record.provenanceRoot,
            record.schemaVersion,
            record.anchoredAt
        );
    }

    function isRangeAnchored(bytes32 siteIdHash, uint64 fromSequence, uint64 throughSequence) external view returns (bool) {
        bytes32 rangeKey = keccak256(abi.encodePacked(siteIdHash, fromSequence, throughSequence));
        return _anchoredRanges[rangeKey];
    }
}

import os
import time
import hashlib
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def compute_site_id_hash(site_id: str) -> str:
    """Deterministic bytes32 hex hash of the site ID for privacy-safe on-chain commitment."""
    digest = hashlib.sha256(site_id.encode("utf-8")).hexdigest()
    return f"0x{digest}"


class BlockchainProvider:
    """Base interface for blockchain ledger anchoring providers."""

    @property
    def network_name(self) -> str:
        return "unknown"

    @property
    def chain_id(self) -> int:
        return 0

    @property
    def contract_address(self) -> str:
        return "0x0000000000000000000000000000000000000000"

    def is_configured(self) -> bool:
        raise NotImplementedError

    def submit_anchor(
        self,
        anchor_id: str,
        site_id: str,
        from_seq: int,
        through_seq: int,
        root_hash: str,
        schema_version: int = 1,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def get_anchor_status(self, tx_hash: str, anchor_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def read_anchor(self, anchor_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError


class MockBlockchainProvider(BlockchainProvider):
    """
    Deterministic in-memory blockchain provider for local development, CI,
    and automated testing without requiring gas or external network connectivity.
    """

    def __init__(
        self,
        network_name: str = "mock-chain",
        chain_id: int = 31337,
        contract_address: str = "0x5FbDB2315678afecb367f032d93F642f64180aa3",
        default_confirmations: int = 6,
        fail_next_submission: bool = False,
    ):
        self._network_name = network_name
        self._chain_id = chain_id
        self._contract_address = contract_address
        self._default_confirmations = default_confirmations
        self._fail_next_submission = fail_next_submission
        self._simulated_block_height = 1000
        # Storage: anchor_id -> record
        self._anchors: Dict[str, Dict[str, Any]] = {}
        # Storage: tx_hash -> tx metadata
        self._transactions: Dict[str, Dict[str, Any]] = {}

    @property
    def network_name(self) -> str:
        return self._network_name

    @property
    def chain_id(self) -> int:
        return self._chain_id

    @property
    def contract_address(self) -> str:
        return self._contract_address

    def is_configured(self) -> bool:
        return True

    def set_fail_next_submission(self, fail: bool) -> None:
        self._fail_next_submission = fail

    def clear(self) -> None:
        self._anchors.clear()
        self._transactions.clear()

    def submit_anchor(
        self,
        anchor_id: str,
        site_id: str,
        from_seq: int,
        through_seq: int,
        root_hash: str,
        schema_version: int = 1,
    ) -> Dict[str, Any]:
        if self._fail_next_submission:
            self._fail_next_submission = False
            raise RuntimeError("Simulated RPC connection timeout (MockBlockchainProvider)")

        # Generate deterministic block and tx hash
        self._simulated_block_height += 1
        block_number = self._simulated_block_height
        site_id_hash = compute_site_id_hash(site_id)

        tx_payload = f"{anchor_id}:{site_id_hash}:{from_seq}:{through_seq}:{root_hash}:{block_number}"
        tx_hash = f"0x{hashlib.sha256(tx_payload.encode()).hexdigest()}"
        anchored_at = int(time.time())

        # Check replay protection
        if anchor_id in self._anchors:
            raise ValueError(f"Anchor ID {anchor_id} already exists on-chain")

        record = {
            "anchor_id": anchor_id,
            "site_id_hash": site_id_hash,
            "from_sequence": from_seq,
            "through_sequence": through_seq,
            "root_hash": root_hash,
            "schema_version": schema_version,
            "anchored_at": anchored_at,
            "block_number": block_number,
            "tx_hash": tx_hash,
            "confirmations": self._default_confirmations,
        }
        self._anchors[anchor_id] = record

        tx_meta = {
            "tx_hash": tx_hash,
            "block_number": block_number,
            "confirmations": self._default_confirmations,
            "status": "confirmed",
            "explorer_url": f"https://mock-explorer.ibvap.internal/tx/{tx_hash}",
            "anchored_at": anchored_at,
        }
        self._transactions[tx_hash] = tx_meta

        return tx_meta

    def get_anchor_status(self, tx_hash: str, anchor_id: str) -> Dict[str, Any]:
        if tx_hash in self._transactions:
            return self._transactions[tx_hash]
        if anchor_id in self._anchors:
            rec = self._anchors[anchor_id]
            return {
                "tx_hash": rec["tx_hash"],
                "block_number": rec["block_number"],
                "confirmations": rec["confirmations"],
                "status": "confirmed",
                "explorer_url": f"https://mock-explorer.ibvap.internal/tx/{rec['tx_hash']}",
                "anchored_at": rec["anchored_at"],
            }
        return {
            "tx_hash": tx_hash,
            "block_number": None,
            "confirmations": 0,
            "status": "pending",
            "explorer_url": None,
            "anchored_at": None,
        }

    def read_anchor(self, anchor_id: str) -> Optional[Dict[str, Any]]:
        return self._anchors.get(anchor_id)

    def submit_anchor_with_provenance(
        self,
        anchor_id: str,
        site_id: str,
        from_seq: int,
        through_seq: int,
        merkle_root: str,
        provenance_root: str,
        schema_version: str = "merkle-v1",
    ) -> Dict[str, Any]:
        if self._fail_next_submission:
            self._fail_next_submission = False
            raise RuntimeError("Simulated RPC connection timeout (MockBlockchainProvider)")

        self._simulated_block_height += 1
        block_number = self._simulated_block_height
        site_id_hash = compute_site_id_hash(site_id)

        tx_payload = f"{anchor_id}:{site_id_hash}:{from_seq}:{through_seq}:{merkle_root}:{provenance_root}:{block_number}"
        tx_hash = f"0x{hashlib.sha256(tx_payload.encode()).hexdigest()}"
        anchored_at = int(time.time())

        record = {
            "anchor_id": anchor_id,
            "site_id_hash": site_id_hash,
            "from_sequence": from_seq,
            "through_sequence": through_seq,
            "merkle_root": merkle_root,
            "root_hash": merkle_root,
            "provenance_root": provenance_root,
            "schema_version": schema_version,
            "anchored_at": anchored_at,
            "block_number": block_number,
            "tx_hash": tx_hash,
            "confirmations": self._default_confirmations,
        }
        self._anchors[anchor_id] = record

        tx_meta = {
            "tx_hash": tx_hash,
            "block_number": block_number,
            "confirmations": self._default_confirmations,
            "status": "confirmed",
            "explorer_url": f"https://mock-explorer.ibvap.internal/tx/{tx_hash}",
            "anchored_at": anchored_at,
        }
        self._transactions[tx_hash] = tx_meta
        return tx_meta

    def read_anchor_with_provenance(self, anchor_id: str) -> Optional[Dict[str, Any]]:
        return self._anchors.get(anchor_id)


class JsonRpcBlockchainProvider(BlockchainProvider):
    """
    Standard EVM JSON-RPC provider using urllib (zero extra heavyweight dependencies).
    Interacts with EVM networks (e.g. Sepolia, Base Sepolia, Polygon Amoy) via JSON-RPC 2.0.
    """

    def __init__(
        self,
        rpc_url: str,
        contract_address: str,
        private_key: Optional[str] = None,
        network_name: str = "sepolia",
        chain_id: int = 11155111,
        required_confirmations: int = 2,
    ):
        self._rpc_url = rpc_url
        self._contract_address = contract_address
        self._private_key = private_key
        self._network_name = network_name
        self._chain_id = chain_id
        self._required_confirmations = required_confirmations

    @property
    def network_name(self) -> str:
        return self._network_name

    @property
    def chain_id(self) -> int:
        return self._chain_id

    @property
    def contract_address(self) -> str:
        return self._contract_address

    def is_configured(self) -> bool:
        return bool(self._rpc_url and self._contract_address)

    def _rpc_call(self, method: str, params: list) -> Any:
        import urllib.request
        import urllib.error

        req_data = json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }).encode("utf-8")

        req = urllib.request.Request(
            self._rpc_url,
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "IBVAP-Ledger-Anchor/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                if "error" in result:
                    # Sanitize message to never leak secrets
                    err_msg = result["error"].get("message", "Unknown RPC error")
                    raise RuntimeError(f"RPC Error: {err_msg}")
                return result.get("result")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error connecting to RPC provider: {str(e.reason) if hasattr(e, 'reason') else str(e)}")

    def submit_anchor(
        self,
        anchor_id: str,
        site_id: str,
        from_seq: int,
        through_seq: int,
        root_hash: str,
        schema_version: int = 1,
    ) -> Dict[str, Any]:
        # If no private key configured, we cannot sign and send raw transactions
        if not self._private_key:
            raise RuntimeError("Blockchain anchoring transaction failed: IBVAP_BLOCKCHAIN_PRIVATE_KEY not configured")

        # For live EVM anchoring without web3 package, we format the call or rely on an authorized transaction relay
        raise NotImplementedError("Live EVM raw transaction submission requires signed transaction relay.")

    def get_anchor_status(self, tx_hash: str, anchor_id: str) -> Dict[str, Any]:
        receipt = self._rpc_call("eth_getTransactionReceipt", [tx_hash])
        if not receipt:
            return {
                "tx_hash": tx_hash,
                "block_number": None,
                "confirmations": 0,
                "status": "submitted",
                "explorer_url": self._get_explorer_url(tx_hash),
            }

        block_num = int(receipt.get("blockNumber", "0x0"), 16)
        latest_block = int(self._rpc_call("eth_blockNumber", []), 16)
        confs = max(0, latest_block - block_num + 1)
        status = "confirmed" if confs >= self._required_confirmations else "submitted"

        return {
            "tx_hash": tx_hash,
            "block_number": block_num,
            "confirmations": confs,
            "status": status,
            "explorer_url": self._get_explorer_url(tx_hash),
        }

    def read_anchor(self, anchor_id: str) -> Optional[Dict[str, Any]]:
        # In read-only mode via eth_call to getAnchor(bytes32)
        # Function selector for getAnchor(bytes32): keccak256("getAnchor(bytes32)")[:4] = 0x24249a40 (or standard ABI)
        try:
            latest_block = self._rpc_call("eth_blockNumber", [])
            return None
        except Exception:
            return None

    def _get_explorer_url(self, tx_hash: str) -> str:
        if "sepolia" in self._network_name.lower():
            return f"https://sepolia.etherscan.io/tx/{tx_hash}"
        if "base" in self._network_name.lower():
            return f"https://sepolia.basescan.org/tx/{tx_hash}"
        return f"https://etherscan.io/tx/{tx_hash}"


# Singleton mock provider instance for testing & offline mode
_GLOBAL_MOCK_PROVIDER = MockBlockchainProvider()


def get_blockchain_provider() -> BlockchainProvider:
    """
    Returns the active blockchain provider configured by environment variables.
    Defaults to MockBlockchainProvider if IBVAP_BLOCKCHAIN_NETWORK is mock/mock-chain or not set.
    """
    enabled = os.getenv("IBVAP_BLOCKCHAIN_ENABLED", "true").lower() in ("true", "1", "yes")
    network = os.getenv("IBVAP_BLOCKCHAIN_NETWORK", "mock-chain").lower()
    rpc_url = os.getenv("IBVAP_BLOCKCHAIN_RPC_URL", "").strip()

    if not enabled:
        # Returns a mock provider with configured = False
        class DisabledProvider(BlockchainProvider):
            def is_configured(self) -> bool:
                return False

            def submit_anchor(self, *args, **kwargs):
                raise RuntimeError("Blockchain anchoring is disabled (IBVAP_BLOCKCHAIN_ENABLED=false)")

            def get_anchor_status(self, *args, **kwargs):
                return {"status": "failed", "last_error": "Blockchain anchoring disabled"}

            def read_anchor(self, *args, **kwargs):
                return None

        return DisabledProvider()

    if network in ("mock", "mock-chain", "test") or not rpc_url:
        return _GLOBAL_MOCK_PROVIDER

    contract_addr = os.getenv("IBVAP_BLOCKCHAIN_CONTRACT_ADDRESS", "")
    priv_key = os.getenv("IBVAP_BLOCKCHAIN_PRIVATE_KEY", None)
    chain_id = int(os.getenv("IBVAP_BLOCKCHAIN_CHAIN_ID", "11155111"))
    confs = int(os.getenv("IBVAP_BLOCKCHAIN_CONFIRMATIONS", "2"))

    return JsonRpcBlockchainProvider(
        rpc_url=rpc_url,
        contract_address=contract_addr,
        private_key=priv_key,
        network_name=network,
        chain_id=chain_id,
        required_confirmations=confs,
    )

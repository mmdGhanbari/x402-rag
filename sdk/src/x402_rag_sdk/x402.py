import base64
import json
import logging
from dataclasses import dataclass
from typing import Any

from solana.rpc.async_api import AsyncClient
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.solders import NullSigner
from solders.transaction import VersionedTransaction
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import (
    TransferCheckedParams,
    get_associated_token_address,
    transfer_checked,
)

from .ata import ensure_ata_exists

logger = logging.getLogger(__name__)

# Default RPCs; override per need
DEFAULT_RPC = {
    "solana": "https://api.mainnet-beta.solana.com",
    "solana-devnet": "https://api.devnet.solana.com",
}

COMPUTE_BUDGET_PROGRAM_ID = Pubkey.from_string("ComputeBudget111111111111111111111111111111")


@dataclass
class X402SolanaConfig:
    """Config for making Solana x402 payments."""

    rpc_by_network: dict[str, str] = None  # e.g. {"solana": "...", "solana-devnet": "..."}

    def __post_init__(self):
        if self.rpc_by_network is None:
            self.rpc_by_network = DEFAULT_RPC


class X402SolanaPayer:
    """Builds a partially-signed USDC transfer tx and returns a base64 X-PAYMENT header."""

    def __init__(self, keypair: Keypair, cfg: X402SolanaConfig):
        self._kp = keypair
        self._cfg = cfg

    @staticmethod
    def _ix_set_cu_limit(units: int) -> Instruction:
        # ComputeBudget program: discriminator 2 + u32 little-endian
        data = bytes([2]) + int(units).to_bytes(4, "little")
        return Instruction(COMPUTE_BUDGET_PROGRAM_ID, data, [])

    @staticmethod
    def _ix_set_cu_price(microlamports_per_cu: int) -> Instruction:
        # ComputeBudget program: discriminator 3 + u64 little-endian
        # NOTE: facilitator caps this at 5_000_000 microlamports per CU.
        data = bytes([3]) + int(microlamports_per_cu).to_bytes(8, "little")
        return Instruction(COMPUTE_BUDGET_PROGRAM_ID, data, [])

    async def build_x_payment_header(
        self,
        *,
        x402_version: int,
        requirements: dict[str, Any],
        asset_decimals: int | None = None,  # default 6 if None
        cu_limit: int = 200_000,
        cu_price_micro_lamports: int = 0,
    ) -> str:
        """
        Build a base64 X-PAYMENT header from a single 'accepts' entry.

        requirements (dict) must include:
            scheme="exact"
            network in {"solana", "solana-devnet"}
            asset = <USDC mint address>
            maxAmountRequired = "<int as string>"
            payTo = <recipient pubkey>
            extra.feePayer = <fee payer pubkey>
        """
        # ---- 1) Pull fields from your requirement ----
        scheme = requirements["scheme"]
        network = requirements["network"]
        mint_str = requirements["asset"]
        pay_to_str = requirements["payTo"]
        amount_raw = int(requirements["maxAmountRequired"])
        fee_payer_str = requirements.get("extra", {}).get("feePayer")

        if scheme != "exact":
            raise ValueError(f"Unsupported scheme: {scheme}")
        if network not in self._cfg.rpc_by_network:
            raise ValueError(f"Unknown network '{network}'. Provide an RPC in rpc_by_network.")
        if not fee_payer_str:
            raise ValueError("requirements.extra.feePayer is required for gasless flow on Solana.")

        decimals = 6 if asset_decimals is None else int(asset_decimals)

        mint = Pubkey.from_string(mint_str)
        recipient = Pubkey.from_string(pay_to_str)
        fee_payer = Pubkey.from_string(fee_payer_str)
        owner = self._kp.pubkey()

        rpc_endpoint = self._cfg.rpc_by_network[network]

        # ---- 2) Resolve ATAs ----
        src_ata = await ensure_ata_exists(
            rpc_url=rpc_endpoint, payer_keypair=self._kp, owner_pubkey=owner, mint_pubkey=mint
        )
        dst_ata = get_associated_token_address(recipient, mint)

        # ---- 3) Build instruction list: [CB limit, CB price, transfer_checked] ----
        ixs = [
            self._ix_set_cu_limit(cu_limit),
            self._ix_set_cu_price(cu_price_micro_lamports),
            transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=src_ata,
                    mint=mint,
                    dest=dst_ata,
                    owner=owner,  # you (token owner) sign
                    amount=amount_raw,
                    decimals=decimals,
                )
            ),
        ]

        # ---- 4) Build a versioned tx (payer = facilitator) and partial-sign (owner only) ----
        async with AsyncClient(rpc_endpoint) as rpc:
            recent_blockhash = (await rpc.get_latest_blockhash()).value.blockhash

        msg = MessageV0.try_compile(
            payer=fee_payer,  # facilitator pays fees but must NOT appear in instruction accounts
            instructions=ixs,
            address_lookup_table_accounts=[],
            recent_blockhash=recent_blockhash,
        )

        # Sign ONLY with the token owner; facilitator (fee payer) will co-sign and submit
        tx = VersionedTransaction(msg, [self._kp, NullSigner(fee_payer)])

        # ---- 5) Encode and wrap into PaymentPayload dict ----
        tx_b64 = base64.b64encode(bytes(tx)).decode("utf-8")

        payment_payload = {
            "x402Version": x402_version,
            "scheme": "exact",
            "network": network,
            "payload": {
                "transaction": tx_b64,
            },
        }

        return base64.b64encode(json.dumps(payment_payload).encode("utf-8")).decode("utf-8")


async def build_x_payment_from_402_json(
    payer: X402SolanaPayer,
    x402_body: dict[str, Any],
    select_requirement=lambda accepts: accepts[0],
    asset_decimals: int | None = None,
) -> tuple[str, int, str]:
    """
    Helper that:
      1) picks a PaymentRequirements entry from the 402 response JSON,
      2) builds the X-PAYMENT header via X402SolanaPayer.

    Returns:
        Tuple of (X-PAYMENT header, paid_amount, pay_to address)
    """
    x402_version = x402_body["x402Version"]
    req = select_requirement(x402_body["accepts"])

    # Extract payment info
    paid_amount = int(req["maxAmountRequired"])
    pay_to = req["payTo"]

    x_payment_header = await payer.build_x_payment_header(
        x402_version=x402_version,
        requirements=req,
        asset_decimals=asset_decimals,
    )

    return x_payment_header, paid_amount, pay_to

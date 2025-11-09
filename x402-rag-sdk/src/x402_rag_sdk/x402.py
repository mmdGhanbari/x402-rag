import base64
import json
from dataclasses import dataclass
from typing import Any

from solana.rpc.async_api import AsyncClient
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import (
    create_idempotent_associated_token_account,
    get_associated_token_address,
    transfer_checked,
)

# Default RPCs; override per need
DEFAULT_RPC = {
    "solana": "https://api.mainnet-beta.solana.com",
    "solana-devnet": "https://api.devnet.solana.com",
}


@dataclass
class X402SolanaConfig:
    """Config for making Solana x402 payments."""

    secret_key_hex: str  # 32-byte seed hex OR 64-byte keypair hex
    rpc_by_network: dict[str, str] = None  # e.g. {"solana": "...", "solana-devnet": "..."}

    def __post_init__(self):
        if self.rpc_by_network is None:
            self.rpc_by_network = DEFAULT_RPC


class X402SolanaPayer:
    """Builds a partially-signed USDC transfer tx and returns a base64 X-PAYMENT header."""

    def __init__(self, cfg: X402SolanaConfig):
        sk = bytes.fromhex(cfg.secret_key_hex)
        # 32 bytes -> seed; 64 bytes -> full keypair (secret+public)
        self._kp = Keypair.from_seed(sk) if len(sk) == 32 else Keypair.from_bytes(sk)
        self._cfg = cfg

    async def build_x_payment_header(
        self,
        *,
        x402_version: int,
        requirements: dict[str, Any],
        asset_decimals: int | None = None,  # default 6 if None
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

        # ---- 2) Build ATAs + transfer_checked ----
        src_ata = get_associated_token_address(owner, mint)
        dst_ata = get_associated_token_address(recipient, mint)

        ixs = [
            # Idempotent ATA creations (payer = facilitator/fee_payer)
            create_idempotent_associated_token_account(payer=fee_payer, owner=owner, mint=mint),
            create_idempotent_associated_token_account(payer=fee_payer, owner=recipient, mint=mint),
            # USDC transfer with checked decimals
            transfer_checked(
                program_id=TOKEN_PROGRAM_ID,
                source=src_ata,
                mint=mint,
                dest=dst_ata,
                owner=owner,  # you (token owner) sign
                amount=amount_raw,
                decimals=decimals,
            ),
        ]

        # ---- 3) Build a versioned tx (payer = facilitator) and partial-sign (owner only) ----
        rpc_endpoint = self._cfg.rpc_by_network[network]
        async with AsyncClient(rpc_endpoint) as rpc:
            bh = (await rpc.get_latest_blockhash()).value.blockhash
        recent = Hash.from_string(bh)

        msg = MessageV0.try_compile(
            payer=fee_payer,
            instructions=ixs,
            address_lookup_table_accounts=[],
            recent_blockhash=recent,
        )

        # Sign ONLY with the token owner; facilitator (fee payer) will co-sign and submit
        tx = VersionedTransaction(msg, [self._kp])

        # ---- 4) Encode and wrap into PaymentPayload dict ----
        payload_b64 = base64.b64encode(bytes(tx)).decode("utf-8")

        payment_payload = {
            "version": x402_version,
            "scheme": "exact",
            "network": network,
            "payload": payload_b64,  # base64-encoded VersionedTransaction bytes
            "requirements": requirements,  # echo the reqs to satisfy matching on the server
        }

        return base64.b64encode(json.dumps(payment_payload).encode("utf-8")).decode("utf-8")


async def build_x_payment_from_402_json(
    payer: X402SolanaPayer,
    x402_body: dict[str, Any],
    select_requirement=lambda accepts: accepts[0],
    asset_decimals: int | None = None,
) -> str:
    """
    Helper that:
      1) picks a PaymentRequirements entry from the 402 response JSON,
      2) builds the X-PAYMENT header via X402SolanaPayer.
    """
    x402_version = x402_body["x402Version"]
    req = select_requirement(x402_body["accepts"])
    return await payer.build_x_payment_header(
        x402_version=x402_version,
        requirements=req,
        asset_decimals=asset_decimals,
    )

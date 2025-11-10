from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from spl.token.instructions import create_idempotent_associated_token_account, get_associated_token_address


async def ensure_ata_exists(
    *,
    rpc_url: str,
    payer_keypair: Keypair,
    owner_pubkey: Pubkey,
    mint_pubkey: Pubkey,
) -> Pubkey:
    """
    Ensures the owner's ATA for `mint_pubkey` exists.
    If missing, creates it in a separate tx where the owner is the payer.
    Returns the ATA address.
    """
    payer = payer_keypair.pubkey()
    ata = get_associated_token_address(owner_pubkey, mint_pubkey)

    async with AsyncClient(rpc_url) as rpc:
        # 1) Check if ATA already exists
        info = await rpc.get_account_info(ata)
        if info.value is not None:
            return ata

        # 2) Build idempotent ATA create (payer = owner)
        ix = create_idempotent_associated_token_account(
            payer=payer,
            owner=owner_pubkey,
            mint=mint_pubkey,
        )

        # 3) Recent blockhash
        recent_blockhash = (await rpc.get_latest_blockhash()).value.blockhash

        # 4) Message + tx: payer is the owner (not the facilitator)
        msg = MessageV0.try_compile(
            payer=payer,
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=recent_blockhash,
        )
        tx = VersionedTransaction(msg, [payer_keypair])

        # 5) Send and (optionally) confirm
        _sig = await rpc.send_raw_transaction(bytes(tx))
        # Optional lightweight confirm loop:
        # await rpc.confirm_transaction(sig.value)

        return ata

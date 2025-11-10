"""Solana-based authentication for X402 RAG SDK."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator
from solders.keypair import Keypair

CANON_PREFIX = "solana-auth-v1"


def iso_utc(dt: datetime) -> str:
    dt = dt.astimezone(UTC).replace(microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


class AuthMessage(BaseModel):
    version: int = Field(..., alias="v")
    uri: str
    issued_at: datetime = Field(..., alias="issuedAt")

    @field_validator("issued_at", mode="before")
    @classmethod
    def ensure_tz(cls, v):
        if isinstance(v, datetime):
            return v if v.tzinfo else v.replace(tzinfo=UTC)
        return v

    def canonical_string(self) -> bytes:
        lines = [
            CANON_PREFIX,
            f"version: {self.version}",
            f"uri: {self.uri}",
            f"issued-at: {iso_utc(self.issued_at)}",
        ]
        return ("\n".join(lines)).encode("utf-8")

    def export_public_dict(self) -> dict:
        return {
            "v": self.version,
            "uri": str(self.uri),
            "issuedAt": iso_utc(self.issued_at),
        }


def build_solana_authorization_header(
    keypair: Keypair,
    uri: str,
    version: int = 1,
    issued_at: datetime | None = None,
) -> str:
    """Build Solana authorization header.

    Returns: 'Solana ' + base64url(JSON({ address, msg, sig }))
    """
    msg = AuthMessage(
        v=version,
        uri=uri,
        issuedAt=issued_at or datetime.now(UTC),
    )
    to_sign = msg.canonical_string()
    sig = keypair.sign_message(to_sign)

    payload = {
        "address": str(keypair.pubkey()),
        "msg": msg.export_public_dict(),
        "sig": b64u(bytes(sig)),
    }

    wire = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return "Solana " + b64u(wire)

"""Solana-based authentication for X402 RAG server."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from pydantic import BaseModel, Field, ValidationError, field_validator
from solders.pubkey import Pubkey

CANON_PREFIX = "solana-auth-v1"


def iso_utc(dt: datetime) -> str:
    dt = dt.astimezone(UTC).replace(microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


def b64u_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


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


class WirePayload(BaseModel):
    address: str
    msg: dict
    sig: str


class AuthError(Exception):
    """Authentication error."""


def verify_solana_authorization_header(
    header_value: str,
    request_uri: str,
    max_ttl_seconds: int = 300,
    clock_skew_seconds: int = 120,
) -> str:
    """Verify Solana authorization header.

    Returns the wallet address (base58) if verification passes.
    Raises AuthError on any failure.
    """
    if not header_value.startswith("Solana "):
        raise AuthError("Unsupported scheme")

    try:
        payload = json.loads(b64u_decode(header_value.split(" ", 1)[1]))
        wire = WirePayload(**payload)
    except Exception as e:
        raise AuthError(f"Bad auth payload: {e}") from e

    try:
        msg = AuthMessage(**wire.msg)
    except ValidationError as e:
        raise AuthError(f"Bad msg: {e}") from e

    if str(msg.uri) != request_uri:
        raise AuthError("URI mismatch")

    now = datetime.now(UTC)
    issued = msg.issued_at if msg.issued_at.tzinfo else msg.issued_at.replace(tzinfo=UTC)

    if issued - now > timedelta(seconds=clock_skew_seconds):
        raise AuthError("issued_at is in the future")
    if now - issued > timedelta(seconds=max_ttl_seconds + clock_skew_seconds):
        raise AuthError("message expired")

    try:
        pubkey = Pubkey.from_string(wire.address)
    except Exception as e:
        raise AuthError("Invalid address") from e

    canonical = msg.canonical_string()
    try:
        VerifyKey(bytes(pubkey)).verify(canonical, b64u_decode(wire.sig))
    except (BadSignatureError, Exception) as e:
        raise AuthError("Signature verify failed") from e

    return wire.address

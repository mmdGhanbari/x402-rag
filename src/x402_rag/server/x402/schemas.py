from pydantic import BaseModel

from x402.types import PaymentPayload as X402PaymentPayload
from x402.types import PaymentRequirements as X402PaymentRequirements
from x402_rag.core import SupportedNetworks


class SchemePayloads(BaseModel):
    transaction: str


class PaymentPayload(X402PaymentPayload):
    payload: SchemePayloads


class PaymentRequirements(X402PaymentRequirements):
    network: SupportedNetworks

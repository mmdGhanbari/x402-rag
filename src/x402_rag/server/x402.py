import base64
import json
import logging
from dataclasses import dataclass
from typing import cast

from fastapi import Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from x402.common import (
    find_matching_payment_requirements,
    x402_VERSION,
)
from x402.encoding import safe_base64_decode
from x402.facilitator import FacilitatorClient, FacilitatorConfig
from x402.paywall import get_paywall_html, is_browser_request
from x402.types import (
    PaymentPayload,
    PaymentRequirements,
    PaywallConfig,
    SupportedNetworks,
    x402PaymentRequiredResponse,
)

from x402_rag.core.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class PaymentContext:
    """Context object holding payment verification state."""

    payment: PaymentPayload
    requirements: PaymentRequirements
    facilitator: FacilitatorClient
    is_verified: bool = False


class X402PaymentRequired(Exception):
    """Exception to indicate payment is required or invalid."""

    def __init__(self, response: JSONResponse | HTMLResponse):
        self.response = response
        super().__init__("Payment required")


class X402PaymentHandler:
    """Handles x402 payment verification and settlement."""

    def __init__(
        self,
        settings: Settings,
        paywall_config: PaywallConfig | None = None,
    ):
        """
        Initialize payment handler.

        Args:
            settings: Application settings containing x402 configuration
            paywall_config: Optional paywall UI configuration
        """
        self.settings = settings
        self.facilitator = FacilitatorClient(FacilitatorConfig(url=settings.x402.facilitator_url))
        self.paywall_config = paywall_config

        # Validate network
        if settings.x402.network not in cast(tuple, SupportedNetworks.__args__):
            raise ValueError(
                f"Unsupported network: {settings.x402.network}. Must be one of: {SupportedNetworks.__args__}"
            )

    def create_payment_requirements(
        self,
        total_price: int,
        resource: str,
        description: str = "",
        mime_type: str = "application/json",
        max_timeout_seconds: int = 60,
    ) -> PaymentRequirements:
        """
        Create payment requirements based on chunk prices.

        Args:
            total_price: Total price in USDC base units
            resource: Resource URL
            description: Description of what is being purchased
            mime_type: MIME type of the response
            max_timeout_seconds: Maximum time allowed for payment

        Returns:
            PaymentRequirements object
        """

        return PaymentRequirements(
            scheme="exact",
            network=cast(SupportedNetworks, self.settings.x402.network),
            asset=self.settings.x402.usdc_address,
            max_amount_required=total_price,
            resource=resource,
            description=description,
            mime_type=mime_type,
            pay_to=self.settings.x402.pay_to_address,
            max_timeout_seconds=max_timeout_seconds,
            extra={
                "feePayer": self.settings.x402.fee_payer,
            },
        )

    def _create_402_response(
        self,
        error: str,
        payment_requirements: PaymentRequirements,
        request: Request,
    ) -> JSONResponse | HTMLResponse:
        """Create a 402 Payment Required response."""
        request_headers = dict(request.headers)

        if is_browser_request(request_headers):
            html_content = get_paywall_html(error, [payment_requirements], self.paywall_config)
            return HTMLResponse(
                content=html_content,
                status_code=402,
                headers={"Content-Type": "text/html; charset=utf-8"},
            )

        response_data = x402PaymentRequiredResponse(
            x402_version=x402_VERSION,
            accepts=[payment_requirements],
            error=error,
        ).model_dump(by_alias=True)
        return JSONResponse(
            content=response_data,
            status_code=402,
            headers={"Content-Type": "application/json"},
        )

    async def verify_payment(
        self,
        request: Request,
        total_price: int,
        description: str = "",
    ) -> PaymentContext:
        """
        Verify payment for retrieving chunks.

        Args:
            request: FastAPI request object
            total_price: Total price in USDC base units
            description: Description of what is being purchased

        Returns:
            PaymentContext with verified payment information

        Raises:
            X402PaymentRequired: If payment is missing, invalid, or insufficient
        """
        # Skip payment check if x402 is disabled
        if not self.settings.x402.enabled:
            # Return a dummy context when payments are disabled
            return PaymentContext(
                payment=PaymentPayload(signature="", eip712_payload={}),
                requirements=PaymentRequirements(
                    scheme="exact",
                    network=cast(SupportedNetworks, self.settings.x402.network),
                    asset=self.settings.x402.usdc_address,
                    max_amount_required=0,
                    resource="",
                    pay_to="",
                ),
                facilitator=self.facilitator,
                is_verified=False,
            )

        resource_url = str(request.url)
        payment_requirements = self.create_payment_requirements(
            total_price=total_price,
            resource=resource_url,
            description=description,
        )

        # Check for payment header
        payment_header = request.headers.get("X-PAYMENT", "")
        if not payment_header:
            raise X402PaymentRequired(
                self._create_402_response("No X-PAYMENT header provided", payment_requirements, request)
            )

        # Decode payment header
        try:
            payment_dict = json.loads(safe_base64_decode(payment_header))
            payment = PaymentPayload(**payment_dict)
        except Exception as e:
            client_host = request.client.host if request.client else "unknown"
            logger.warning(f"Invalid payment header from {client_host}: {str(e)}")
            raise X402PaymentRequired(
                self._create_402_response("Invalid payment header format", payment_requirements, request)
            ) from e

        # Find matching payment requirements
        if not find_matching_payment_requirements([payment_requirements], payment):
            raise X402PaymentRequired(
                self._create_402_response(
                    "Payment does not match requirements", payment_requirements, request
                )
            )

        # Verify payment with facilitator
        try:
            verify_response = await self.facilitator.verify(payment, payment_requirements)
        except Exception as e:
            logger.error(f"Failed to verify payment: {e}")
            raise X402PaymentRequired(
                self._create_402_response(
                    f"Payment verification failed: {str(e)}",
                    payment_requirements,
                    request,
                )
            ) from e

        if not verify_response.is_valid:
            error_reason = verify_response.invalid_reason or "Unknown error"
            raise X402PaymentRequired(
                self._create_402_response(
                    f"Invalid payment: {error_reason}",
                    payment_requirements,
                    request,
                )
            )

        # Return verified payment context
        return PaymentContext(
            payment=payment,
            requirements=payment_requirements,
            facilitator=self.facilitator,
            is_verified=True,
        )

    async def settle_payment(self, payment_ctx: PaymentContext, response: Response) -> None:
        """
        Settle a verified payment and set the X-PAYMENT-RESPONSE header.

        Args:
            payment_ctx: PaymentContext from verify_payment
            response: FastAPI Response object to set header on

        Raises:
            X402PaymentRequired: If settlement fails
        """
        # Skip settlement if x402 is disabled or payment wasn't verified
        if not self.settings.x402.enabled or not payment_ctx.is_verified:
            return

        try:
            settle_response = await payment_ctx.facilitator.settle(
                payment_ctx.payment, payment_ctx.requirements
            )

            if settle_response.success:
                json_data = settle_response.model_dump_json(by_alias=True)
                settlement_header = base64.b64encode(json_data.encode("utf-8")).decode("utf-8")
                response.headers["X-PAYMENT-RESPONSE"] = settlement_header
                return

            error_reason = settle_response.error_reason or "Unknown error"
            error_msg = f"Settlement failed: {error_reason}"
            logger.error(error_msg)
            raise X402PaymentRequired(JSONResponse(content={"error": error_msg}, status_code=402)) from None
        except X402PaymentRequired:
            raise
        except Exception as e:
            logger.error(f"Settlement failed: {e}")
            raise X402PaymentRequired(
                JSONResponse(
                    content={"error": f"Settlement failed: {str(e)}"},
                    status_code=402,
                )
            ) from e

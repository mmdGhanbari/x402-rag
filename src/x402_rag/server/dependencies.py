from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from x402_rag.core import RuntimeContext, Settings
from x402_rag.services import DocIndexService, RetrievalService, WebIndexService

from .auth import AuthError, verify_solana_authorization_header
from .simple_di import DiContainer, container, inject_container
from .x402 import X402PaymentHandler

ContainerDep = Annotated[DiContainer, Depends(inject_container)]


async def get_user_address(
    request: Request,
    authorization: str | None = Header(None),
) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        full_uri = str(request.url)
        address = verify_solana_authorization_header(
            header_value=authorization,
            request_uri=full_uri,
        )
        return address
    except AuthError as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}") from e


UserAddressDep = Annotated[str, Depends(get_user_address)]


def get_settings() -> Settings:
    return container.resolve_sync(Settings)


container.register(Settings, resolver=lambda: Settings())

container.register(
    RuntimeContext,
    resolver=lambda settings: RuntimeContext.create(settings),
    deps=[Settings],
)

container.register(
    DocIndexService,
    deps=[RuntimeContext],
    resolver=lambda ctx: DocIndexService(ctx),
)
container.register(
    WebIndexService,
    deps=[RuntimeContext],
    resolver=lambda ctx: WebIndexService(ctx),
)
container.register(
    RetrievalService,
    deps=[RuntimeContext],
    resolver=lambda ctx: RetrievalService(ctx),
)

container.register(
    X402PaymentHandler,
    deps=[Settings],
    resolver=lambda settings: X402PaymentHandler(settings),
)

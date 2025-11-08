from typing import Annotated

from fastapi import Depends

from x402_rag.core import RuntimeContext, Settings
from x402_rag.services import DocIndexService, RetrievalService, WebIndexService

from .simple_di import DiContainer, container, inject_container

ContainerDep = Annotated[DiContainer, Depends(inject_container)]


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

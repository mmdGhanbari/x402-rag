from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

# Gets resolved dependencies as variable arguments and returns a provider
type ProviderResolver[T] = Callable[..., T | Coroutine[Any, Any, T]]


@dataclass
class ProviderFactory[T]:
    deps: list[type]
    resolver: ProviderResolver[T]


class DiContainer:
    providers: dict[type, Any]
    factories: dict[type, ProviderFactory[Any]]

    def __init__(self):
        self.providers = {}
        self.factories = {}

    def register(
        self,
        type: type,
        *,
        deps: list[type] | None = None,
        resolver: ProviderResolver[Any] | None = None,
    ):
        self.factories[type] = ProviderFactory(
            deps=deps or [],
            resolver=resolver or (lambda: type()),
        )

    def resolve_sync[T](self, target_type: type[T]) -> T:
        if target_type in self.providers:
            return self.providers[target_type]

        if target_type not in self.factories:
            raise ValueError(f"No factory registered for {target_type}")

        factory = self.factories[target_type]

        resolved_deps = [self.resolve_sync(dep) for dep in factory.deps]

        provider = factory.resolver(*resolved_deps)
        if isinstance(provider, Coroutine):
            raise ValueError(f"[resolve_sync] Resolver for {target_type} returned a coroutine")

        self.providers[target_type] = provider
        return provider

    async def resolve[T](self, target_type: type[T]) -> T:
        if target_type in self.providers:
            return self.providers[target_type]

        if target_type not in self.factories:
            raise ValueError(f"No factory registered for {target_type}")

        factory = self.factories[target_type]

        resolved_deps = [await self.resolve(dep) for dep in factory.deps]

        result = factory.resolver(*resolved_deps)
        provider = await result if isinstance(result, Coroutine) else result

        self.providers[target_type] = provider

        return provider


container = DiContainer()


def inject_container() -> DiContainer:
    return container

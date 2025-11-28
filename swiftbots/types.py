from collections.abc import AsyncGenerator, Callable
from typing import Any, TypeVar


class DependencyContainer:
    def __init__(self, dependency: Callable[..., Any]):
        self.dependency = dependency


DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
AsyncSenderFunction = TypeVar("AsyncSenderFunction", bound=Callable[[str, str | int], Any])
AsyncListenerFunction = TypeVar("AsyncListenerFunction", bound=AsyncGenerator[Any, dict])

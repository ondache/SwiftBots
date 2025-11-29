from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from swiftbots.bots import Bot


class DependencyContainer:
    def __init__(self, dependency: Callable[..., Any]):
        self.dependency = dependency


DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
AsyncSenderFunction = TypeVar("AsyncSenderFunction", bound=Callable[[str, str | int], Any])
AsyncListenerFunction = TypeVar("AsyncListenerFunction", bound=AsyncGenerator[Any, dict])
CallNextMiddleware = Callable[[Any], Coroutine]
Middleware = Callable[['Bot', Any, CallNextMiddleware], Coroutine]

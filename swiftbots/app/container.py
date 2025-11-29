from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from swiftbots.all_types import ILogger, IScheduler
    from swiftbots.bots import Bot


class AppContainer:
    def __init__(self, bots: list['Bot'], logger: 'ILogger', scheduler: 'IScheduler', run_with: dict[str, Any]) -> None:
        self.bots = bots
        self.logger = logger
        self.scheduler = scheduler
        self.run_with = run_with

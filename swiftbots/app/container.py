from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiftbots.all_types import ILogger, IScheduler
    from swiftbots.bots import Bot

@dataclass
class AppContainer:
    bots: list['Bot']
    logger: 'ILogger'
    scheduler: 'IScheduler'

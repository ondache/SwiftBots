from dataclasses import dataclass

from swiftbots.all_types import ITrigger
from swiftbots.types import DecoratedCallable


@dataclass
class TaskInfo:
    name: str
    func: DecoratedCallable
    triggers: list[ITrigger]
    run_at_start: bool

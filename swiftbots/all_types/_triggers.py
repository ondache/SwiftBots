from abc import ABC, abstractmethod
from datetime import timedelta


class ITrigger(ABC):
    ...


class IPeriodTrigger(ITrigger, ABC):
    hours: float | None
    minutes: float | None
    seconds: float | None

    @abstractmethod
    def __init__(self,
                 hours: float | None = None,
                 minutes: float | None = None,
                 seconds: float | None = None,
                 ):
        """:param hours: how many hours period. It will add to other parameters.
        :param minutes: how many minutes period. It will add to other parameters.
        :param seconds: how many seconds period. It will add to other parameters.
        """
        ...

    @abstractmethod
    def get_period(self) -> timedelta:
        ...

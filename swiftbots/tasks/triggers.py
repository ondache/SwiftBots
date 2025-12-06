from datetime import timedelta

from swiftbots.all_types import IPeriodTrigger


class PeriodTrigger(IPeriodTrigger):
    def __init__(self,
                 hours: float = 0,
                 minutes: float = 0,
                 seconds: int = 0,
                 ):
        if hours < 0 or minutes < 0 or seconds < 0:
            msg = 'Time for scheduler must be positive or zero'
            raise ValueError(msg)
        self.__period = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    def get_period(self) -> timedelta:
        return self.__period

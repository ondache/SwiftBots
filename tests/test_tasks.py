import asyncio

import pytest

from swiftbots import PeriodTrigger, StubBot, SwiftBots, depends
from tests.common import close_test_app, run_raisable

global_var = 0


class Changer:
    async def change_var(self, value):
        await asyncio.sleep(0)
        global global_var
        global_var = value
        close_test_app()


class TestTasks:

    @pytest.mark.timeout(5)
    def test_task(self):
        app = SwiftBots()

        bot = StubBot()

        @bot.task(PeriodTrigger(seconds=2), run_at_start=False, name='my-task')
        async def my_task_method(changer: Changer = depends(lambda: Changer())):
            await changer.change_var(5)

        app.add_bots([bot])

        run_raisable(app)

        global global_var
        assert global_var == 5

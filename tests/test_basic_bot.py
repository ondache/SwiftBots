import asyncio

import pytest

from swiftbots import Bot, SwiftBots
from tests.common import close_test_app, run_raisable, extract_exception_handler_middlewares

global_dict = {}


bot = Bot()
extract_exception_handler_middlewares(bot)


@bot.handler()
async def the_one_handler(value: str):
    await asyncio.sleep(0)
    global global_dict
    global_dict['value'] = value
    close_test_app()


@bot.listener()
async def listen_async():
    await asyncio.sleep(0)
    test_value = 'Some value'
    yield {
        "value": test_value
    }


class TestBasicBot:

    @pytest.mark.timeout(3)
    def test_base_handler(self):
        app = SwiftBots()

        app.add_bots([bot])

        run_raisable(app)

        global global_dict
        assert global_dict['value'] == 'Some value'

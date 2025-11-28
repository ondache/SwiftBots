import asyncio

import pytest

from swiftbots import Bot, StubBot, SwiftBots
from swiftbots.admin_utils import get_bot_names_async, shutdown_app, shutdown_bot_async, start_bot_async

STUB_BOT_NAME = 'bot1'
ADMIN_BOT_NAME = 'admin'


class TestAdminUtils:

    @pytest.mark.timeout(3)
    def test_stop(self):
        app = SwiftBots()

        bot = Bot(name=ADMIN_BOT_NAME)
        bots_list = set()

        @bot.handler()
        async def handler():
            await asyncio.sleep(0)
            await shutdown_bot_async(STUB_BOT_NAME)
            nonlocal bots_list
            _, _, bots_list = await get_bot_names_async()
            shutdown_app()

        @bot.listener()
        async def listen():
            while True:
                await asyncio.sleep(0)
                yield {}

        app.add_bots([
            bot,
            StubBot(name=STUB_BOT_NAME)
        ])

        app.run()

        assert bots_list == {STUB_BOT_NAME}


    @pytest.mark.timeout(3)
    def test_list(self):
        app = SwiftBots()

        bot = Bot(name=ADMIN_BOT_NAME)
        bots_list = tuple()

        @bot.handler()
        async def handler():
            await asyncio.sleep(0)
            nonlocal bots_list
            bots_list = await get_bot_names_async()
            shutdown_app()

        @bot.listener()
        async def listen():
            while True:
                await asyncio.sleep(0)
                yield {}

        app.add_bots([
            bot,
            StubBot(name=STUB_BOT_NAME, run_at_start=False)
        ])

        app.run()

        assert bots_list == ({ADMIN_BOT_NAME, STUB_BOT_NAME}, {ADMIN_BOT_NAME}, {STUB_BOT_NAME})


    @pytest.mark.timeout(3)
    def test_start(self):
        app = SwiftBots()

        bot = Bot(name=ADMIN_BOT_NAME)
        bots_list = set()

        @bot.handler()
        async def handler():
            await asyncio.sleep(0)
            await start_bot_async(STUB_BOT_NAME)
            nonlocal bots_list
            _, bots_list, _ = await get_bot_names_async()
            shutdown_app()

        @bot.listener()
        async def listen():
            while True:
                await asyncio.sleep(0)
                yield {}

        app.add_bots([
            bot,
            StubBot(name=STUB_BOT_NAME, run_at_start=False)
        ])

        app.run()

        assert bots_list == {ADMIN_BOT_NAME, STUB_BOT_NAME}

import asyncio
import sys

from swiftbots.all_types import (
    ExitApplicationException,
    ExitBotException,
    IScheduler,
    RestartListeningException,
    StartBotException,
)
from swiftbots.app.container import AppContainer
from swiftbots.bots import Bot, build_scheduler, stop_bot_async
from swiftbots.middlewares import compose_middlewares
from swiftbots.utils import ErrorRateMonitor, error_rate_monitors

__ALL_TASKS: set[str] = set()
__SCHEDULER_TASK_NAME = '__sched__'


def get_all_tasks() -> set[str]:
    return __ALL_TASKS


async def start_async_listener(bot: Bot) -> None:
    """Launches all bot listeners, and sends all updates to their handlers.
    Runs asynchronously.
    """
    error_rate_monitors.set(ErrorRateMonitor(cooldown=60))
    generator = bot.listener_func()
    middlewares = bot._middlewares
    entry = compose_middlewares(bot, middlewares)
    while True:
        generator = await entry(generator)


async def start_bot(bot: Bot, scheduler: IScheduler) -> None:
    bot.enable()
    build_scheduler([bot], scheduler)
    await start_async_listener(bot)


async def start_async_loop(app_container: AppContainer) -> None:
    bots = app_container.bots
    for bot in bots:
        await bot.before_start_async()

    sched = app_container.scheduler
    tasks: set[asyncio.Task] = set()

    bots_dict: dict[str, Bot] = {bot.name: bot for bot in bots}
    global __ALL_TASKS
    __ALL_TASKS = set(bots_dict.keys())

    # Create tasks for the bots' views
    for name, bot in bots_dict.items():
        if bot.run_at_start:
            task = asyncio.create_task(start_async_listener(bot), name=name)
            tasks.add(task)
    # Create a task for the scheduler
    tasks.add(
        asyncio.create_task(sched.start(), name=__SCHEDULER_TASK_NAME),
    )

    while True:
        # if no bots launched, then close the app
        if not any(filter(lambda t: t.get_name() != __SCHEDULER_TASK_NAME, tasks)):
            await app_container.logger.report_async("Bots application's closed. The reason is no bots launched now.")
            for bot_to_close in bots:
                await bot_to_close.before_close_async()
            sys.exit(1)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            name = task.get_name()
            logger = bots_dict[name].logger if name != __SCHEDULER_TASK_NAME else app_container.logger
            try:
                result = task.result()
                await logger.critical_async(
                    f"Bot {name} is finished with result {result} and restarted",
                )
            except (asyncio.CancelledError, ExitBotException) as ex:
                if isinstance(ex, asyncio.CancelledError):
                    await logger.warning_async(
                        f"Bot {name} is cancelled. Not started again",
                    )
                    await logger.report_async(f"Bot {name}'s exited")
                elif isinstance(ex, ExitBotException):
                    await logger.error_async(
                        f"Bot {name} is exited with message: {ex}",
                    )
                bot = bots_dict[name]
                await stop_bot_async(bot, sched)
                tasks.remove(task)
            except RestartListeningException:
                tasks.remove(task)
                bot = bots_dict[name]
                new_task = asyncio.create_task(start_async_listener(bot), name=name)
                tasks.add(new_task)
            except StartBotException as ex:
                # Special exception instance for starting bots from admin panel

                # At the start, dispose the task of caller bot and create new.
                # The caller task is no longer reusable because an exception was raised.
                tasks.remove(task)
                bot = bots_dict[name]
                new_task = asyncio.create_task(start_async_listener(bot), name=name)
                tasks.add(new_task)

                # Start a new bot with the name from an exception
                try:
                    bot_name_to_start = str(ex)
                    bot_to_start = bots_dict[str(ex)]
                    new_task = asyncio.create_task(
                        start_bot(bot_to_start, sched), name=bot_name_to_start,
                    )
                    tasks.add(new_task)
                except Exception as e:
                    await logger.critical_async(
                        f"Couldn't start bot {ex}. Exception: {e}",
                    )
            except ExitApplicationException:
                # close all bots
                for a_task in tasks:
                    bot_name_to_exit = a_task.get_name()
                    if bot_name_to_exit != __SCHEDULER_TASK_NAME:
                        bot_to_exit = bots_dict[bot_name_to_exit]
                        await stop_bot_async(bot_to_exit, sched)
                        await bot_to_exit.logger.report_async(
                            f"Bot {bot_to_exit.name}'s exited",
                        )
                for bot_to_close in bots:
                        await bot_to_close.before_close_async()
                await logger.report_async("Bots application's closed")
                sys.exit(0)


def run_async(container: AppContainer) -> None:
    asyncio.run(start_async_loop(container))


async def run_oneshot_async(container: AppContainer) -> None:
    assert len(container.bots) == 1, 'Only one bot is allowed to run oneshot'
    bot = container.bots[0]
    message = container.run_with
    await bot.before_start_async()
    entry = compose_middlewares(bot, bot._middlewares)
    await entry(message)
    await bot.before_close_async()


def run_oneshot(container: AppContainer) -> None:
    asyncio.run(run_oneshot_async(container))

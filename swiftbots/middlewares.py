import asyncio
from traceback import format_exc
from typing import Any, TYPE_CHECKING
from collections.abc import Coroutine, AsyncGenerator

from swiftbots.functions import decompose_bot_as_dependencies, resolve_function_args
from swiftbots.utils import error_rate_monitors
from swiftbots.types import Middleware, CallNextMiddleware
from swiftbots.all_types import RestartListeningException, ExitBotException
from swiftbots.message_handlers import search_best_command_match, is_user_allowed
if TYPE_CHECKING:
    from swiftbots.bots import Bot, ChatBot


def make_layer(bot: 'Bot', cur_layer: Middleware, next_layer: CallNextMiddleware) -> CallNextMiddleware:
    def layer(obj) -> Coroutine:
        return cur_layer(bot, obj, next_layer)
    return layer


def compose_middlewares(bot: 'Bot', middlewares: list[Middleware]) -> CallNextMiddleware:
    next_callable = lambda _: _

    for middleware in reversed(middlewares):
        next_callable = make_layer(bot, middleware, next_callable)
    return next_callable


async def process_listener_exceptions(bot: 'Bot', listen_generator: AsyncGenerator, call_next: CallNextMiddleware) -> AsyncGenerator:
    """
    The middleware prevents non-base exceptions from stopping the app.
    Caught exceptions are logged and processed accordingly to its type.
    Too frequent exceptions cause the bot to sleep for some time.
    Used only for listener functions.
    """
    err_monitor = error_rate_monitors.get()
    try:
        await call_next(listen_generator)
        return listen_generator
    # except (AttributeError, TypeError, KeyError, AssertionError) as e:
    #     await bot.logger.critical_async(f"Fix the code! Critical {e.__class__.__name__} "
    #                                     f"raised: {e}. Full traceback:\n{format_exc()}")
    #     continue
    except RestartListeningException:
        return bot.listener_func()
    except Exception as e:
        await bot.logger.exception_async(
            f"Bot {bot.name} was raised with unhandled `{e.__class__.__name__}`"
            f" and kept listening on:\n{e}.\nFull traceback:\n{format_exc()}"
        )
        if err_monitor.since_start < 3:
            raise ExitBotException(
                f"Bot {bot.name} raises immediately after start listening. "
                "Stopping the bot."
            )
        rate = err_monitor.evoke()
        if rate > 5:
            await bot.logger.error_async(f"Bot {bot.name} sleeps for 30 seconds.")
            await asyncio.sleep(30)
            err_monitor.error_count = 3
        return bot.listener_func()


async def execute_listener(_, listen_generator: AsyncGenerator, call_next: CallNextMiddleware) -> Any:
    """
    The middleware extracts the request from the bot listener and passes it to the next middleware.
    """
    output = await listen_generator.__anext__()
    return await call_next(output)


async def process_handler_exceptions(bot: 'Bot', output: Any, call_next: CallNextMiddleware) -> Any:
    try:
        return await call_next(output)
    except (AttributeError, TypeError, KeyError, AssertionError) as e:
        await bot.logger.critical_async(
            f"Fix the code. Critical `{e.__class__.__name__}` "
            f"raised:\n{e}.\nFull traceback:\n{format_exc()}"
        )
    except Exception as e:
        await bot.logger.exception_async(
            f"Bot {bot.name} was raised with unhandled `{e.__class__.__name__}` "
            f"and kept on working:\n{e}.\nFull traceback:\n{format_exc()}"
        )


async def load_dependencies(bot: 'Bot', output: dict, call_next: CallNextMiddleware) -> Any:
    deps = decompose_bot_as_dependencies(bot)
    deps.update(output)
    return await call_next(deps)


async def call_with_dependencies_injected(_, deps: dict, __) -> Any:
    handler = deps['handler']
    args = resolve_function_args(handler, deps)
    return await handler(**args)


async def load_chat_dependencies(bot: 'ChatBot', deps: dict, call_next: CallNextMiddleware) -> Any:
    deps['raw_message'] = deps['message']
    chat = bot._make_chat(deps)
    deps['chat'] = chat
    return await call_next(deps)


async def route_chat_message(bot: 'ChatBot', deps: dict, call_next: CallNextMiddleware) -> dict:
    trie = bot._trie
    chat = deps['chat']
    message = chat.message
    best_matched_command, match = search_best_command_match(trie, message)

    if best_matched_command and not is_user_allowed(chat.sender, best_matched_command.whitelist_users,
                                                    best_matched_command.blacklist_users):
        return await chat.refuse_async()

    arguments = ""
    # check if the command has arguments like `ADD NOTE apple, cigarettes, cheese`,
    # where `ADD NOTE` is a command and the rest is arguments
    if match:
        message_without_command = match.group(1)
        if message_without_command:
            arguments = message_without_command

    # Found the command. Call the method attached to the command
    if not best_matched_command: # No matches. Send `unknown message`
        return await chat.unknown_command_async()

    command_name = best_matched_command.command_name
    deps['arguments'] = deps['args'] = deps['message'] = arguments
    deps['command'] = command_name
    deps['handler'] = best_matched_command.method
    return await call_next(deps)



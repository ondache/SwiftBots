import asyncio
from collections.abc import AsyncGenerator, Callable
from textwrap import wrap
from traceback import format_exc
from typing import Any, TypeVar

import httpx

from swiftbots.all_types import (
    ExitBotException,
    ILogger,
    ILoggerFactory,
    IScheduler,
    ITrigger,
    RestartListeningException,
)
from swiftbots.chats import Chat, TelegramChat
from swiftbots.functions import (
    decompose_bot_as_dependencies,
    generate_name,
    resolve_function_args,
)
from swiftbots.loggers import SysIOLoggerFactory
from swiftbots.message_handlers import (
    ChatMessageHandler,
    CompiledChatCommand,
    Trie,
    compile_chat_commands,
    insert_trie,
)
from swiftbots.middlewares import (
    call_with_dependencies_injected,
    deconstruct_telegram_message,
    execute_listener,
    load_chat_dependencies,
    load_dependencies,
    process_handler_exceptions,
    process_listener_exceptions,
    route_chat_message,
)
from swiftbots.tasks.tasks import TaskInfo
from swiftbots.types import AsyncListenerFunction, AsyncSenderFunction, DecoratedCallable, Middleware


class Bot:
    """Base class for all other types of bots.
    This bot can only have a listener, a handler or tasks
    """

    listener_func: AsyncListenerFunction
    handler_func: DecoratedCallable
    _middlewares: list[Middleware]

    def __init__(
            self,
            name: str | None = None,
            bot_logger_factory: ILoggerFactory | None = None,
            run_at_start: bool = True,
            middlewares: list[Middleware] | None = None,
    ):
        assert bot_logger_factory is None or isinstance(
            bot_logger_factory, ILoggerFactory,
        ), "Logger must be of type ILoggerFactory"

        self.task_infos: list[TaskInfo] = []
        self.name: str = name or generate_name()
        self.run_at_start: bool = run_at_start
        self._custom_middlewares: list[Middleware] | None = middlewares
        self._user_middlewares: list[Middleware] = []
        self._configure_middlewares()
        bot_logger_factory = bot_logger_factory or SysIOLoggerFactory()
        self.__logger: ILogger = bot_logger_factory.get_logger()
        self.__logger.bot_name = self.name
        self.__is_enabled = True

    @property
    def logger(self) -> ILogger:
        return self.__logger

    @property
    def is_enabled(self) -> bool:
        return self.__is_enabled

    def disable(self) -> None:
        self.__is_enabled = False

    def enable(self) -> None:
        self.__is_enabled = True

    def listener(self) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def wrapper(func: DecoratedCallable) -> DecoratedCallable:
            self.listener_func = func
            return func

        return wrapper

    def handler(self) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def wrapper(func: DecoratedCallable) -> DecoratedCallable:
            self.handler_func = func
            return func

        return wrapper

    def task(
            self,
            triggers: ITrigger | list[ITrigger],
            run_at_start: bool = False,
            name: str | None = None,
    ) -> Callable[[DecoratedCallable], TaskInfo]:
        """Mark a bot method as a task.
        Will be executed by SwiftBots automatically.
        """
        assert isinstance(triggers, ITrigger) or isinstance(triggers, list), \
            'Trigger must be the type of ITrigger or a list of ITriggers'

        if isinstance(triggers, list):
            for trigger in triggers:
                assert isinstance(trigger, ITrigger), 'Triggers must be the type of ITrigger'
        assert isinstance(triggers, ITrigger) or len(triggers) > 0, 'Empty list of triggers'
        if name is None:
            name = generate_name()
        assert isinstance(name, str), 'Name must be a string'

        def wrapper(func: DecoratedCallable) -> TaskInfo:
            task_info = TaskInfo(name=name,
                                 func=func,
                                 triggers=triggers if isinstance(triggers, list) else [triggers],
                                 run_at_start=run_at_start)
            self.task_infos.append(task_info)
            return task_info

        return wrapper

    def middleware(self) -> Callable[[Middleware], Middleware]:
        def wrapper(func: Middleware) -> Middleware:
            self._user_middlewares.append(func)
            self._configure_middlewares()
            return func

        return wrapper

    def assert_configured(self) -> None:
        members = vars(self)
        assert 'listener_func' in members, 'You have to set a listener or use different type of a bot'
        assert 'handler_func' in members, 'You have to set a handler or use different type of a bot'

    async def before_start_async(self) -> None:
        """Do something right before the app starts.
        Need to override this method.
        Use it like `super().before_start_async()`.
        """
        # TODO: do assert, check if listener_func is exist in self

    async def before_close_async(self) -> None:
        ...

    def _configure_middlewares(self) -> None:
        self._middlewares = self._custom_middlewares or [
                process_listener_exceptions,
                execute_listener,
                process_handler_exceptions,
                load_dependencies,
                *self._user_middlewares,
                call_with_dependencies_injected,
            ]


class StubBot(Bot):
    """This class is used as a stub to allow a bot to run without a listener or a handler.
    """

    def __init__(self,
                 name: str | None = None,
                 bot_logger_factory: ILoggerFactory | None = None,
                 run_at_start: bool = True,
                 ):
        super().__init__(name=name, bot_logger_factory=bot_logger_factory, run_at_start=run_at_start)
        self.listener_func = self.stub_listener
        self.handler_func = self.stub_handler

    async def stub_listener(self) -> dict:
        while True:
            await asyncio.sleep(1000000.)
            if False:
                yield {}

    async def stub_handler(self) -> None:
        await asyncio.sleep(0)


class ChatBot(Bot):
    Chat = TypeVar('Chat', bound=Chat)
    _sender_func: AsyncSenderFunction
    _compiled_chat_commands: list[CompiledChatCommand]
    _message_handlers: list[ChatMessageHandler]
    _admin: str | None = None
    _trie: Trie

    def __init__(self,
                 name: str | None = None,
                 bot_logger_factory: ILoggerFactory | None = None,
                 chat_error_message: str = "Error occurred",
                 chat_unknown_error_message: str = "Unknown command",
                 chat_refuse_message: str = "Access forbidden",
                 admin: int | str | None = None,
                 run_at_start: bool = True,
                 middlewares: list[Middleware] | None = None,
                 ):
        super().__init__(name=name,
                         bot_logger_factory=bot_logger_factory,
                         run_at_start=run_at_start,
                         middlewares=middlewares)
        self._message_handlers = []
        self._admin = admin
        self._trie = {}
        self._chat_error_message: str = chat_error_message
        self._chat_unknown_message: str = chat_unknown_error_message
        self._chat_refuse_message: str = chat_refuse_message

    def message_handler(self,
                        commands: list[str],
                        admin_only: bool = False,
                        whitelist_users: list[str | int] | None = None,
                        blacklist_users: list[str | int] | None = None) -> DecoratedCallable:
        """:param commands: commands, that will fire the method. For example: ['add', '+'].
        Message "add 2 2" will execute in this method.
        :param admin_only: only admin will be able to use this command. If True, whitelist_users list will be ignored.
        :param whitelist_users: the only users from the list will be able to use this command. If admin_only = True,
        then whitelist_users will be ignored.
        :param blacklist_users: the users from list won't be able to use this command.
        blacklist has a privilege upon whitelist.
        """
        assert isinstance(commands, list), 'Commands must be a list of strings'
        assert len(commands) > 0, 'Empty list of commands'
        for command in commands:
            assert isinstance(command, str), 'Command must be a string'

        def wrapper(func: DecoratedCallable) -> ChatMessageHandler:
            handler = ChatMessageHandler(commands=commands,
                                         function=func,
                                         whitelist_users=whitelist_users if not admin_only else [self._admin],
                                         blacklist_users=blacklist_users)
            self._message_handlers.append(handler)
            return handler

        return wrapper

    def sender(self) -> Callable[[AsyncSenderFunction], AsyncSenderFunction]:
        def wrapper(func: AsyncSenderFunction) -> AsyncSenderFunction:
            self._sender_func = func
            return func

        return wrapper

    def default_handler(
            self,
            admin_only: bool = False,
            whitelist_users: list[str | int] | None = None,
            blacklist_users: list[str | int] | None = None) -> DecoratedCallable:
        return self.message_handler(
            commands=[''],
            admin_only=admin_only,
            whitelist_users=whitelist_users,
            blacklist_users=blacklist_users)

    def assert_configured(self) -> None:
        members = vars(self)
        assert 'listener_func' in members, 'You have to set a listener or use different type of a bot'
        assert len(self._message_handlers) > 0, 'You have to set at least one message handler or default handler'

    async def before_start_async(self) -> None:
        await super().before_start_async()
        # TODO: do assert, check if listener_func is exist in self
        self._compiled_chat_commands = compile_chat_commands(self._message_handlers)
        self._message_handlers.clear()
        for command in self._compiled_chat_commands:
            insert_trie(self._trie, command.command_name.lower(), command)

    def handler_func(self) -> None:
        msg = "You should use message handler or default handler for ChatBot"
        raise NotImplementedError(msg)

    def _configure_middlewares(self) -> None:
        self._middlewares = self._custom_middlewares or [
                process_listener_exceptions,
                execute_listener,
                process_handler_exceptions,
                load_dependencies,
                load_chat_dependencies,
                route_chat_message,
                *self._user_middlewares,
                call_with_dependencies_injected,
            ]

    def _make_chat(self, deps: dict) -> Chat:
        return Chat(
            sender=deps['sender'],
            message=deps['raw_message'],
            function_sender=self._sender_func,
            logger=self.logger,
            error_message=self._chat_error_message,
            unknown_message=self._chat_unknown_message,
            refuse_message=self._chat_refuse_message,
        )


class TelegramBot(ChatBot):
    Chat = TypeVar('Chat', bound=TelegramChat)
    __token: str
    __http_session: httpx.AsyncClient
    __first_time_launched = True
    ALLOWED_UPDATES = ["messages"]

    def __init__(self,
                 token: str,
                 admin: int | str | None = None,
                 name: str | None = None,
                 bot_logger_factory: ILoggerFactory | None = None,
                 greeting_enabled: bool = True,
                 skip_old_updates: bool = True,
                 chat_error_message: str = "Error occurred",
                 chat_unknown_error_message: str = "Unknown command",
                 chat_refuse_message: str = "Access forbidden",
                 run_at_start: bool = True,
                 middlewares: list[Middleware] | None = None,
                 ):
        super().__init__(name=name,
                         bot_logger_factory=bot_logger_factory,
                         chat_error_message=chat_error_message,
                         chat_unknown_error_message=chat_unknown_error_message,
                         chat_refuse_message=chat_refuse_message,
                         admin=admin,
                         run_at_start=run_at_start,
                         middlewares=middlewares)
        self.__token = token
        self.__greeting_enabled = greeting_enabled
        self._sender_func = self._send_async
        self.__should_skip_old_updates = skip_old_updates
        self.listener_func = self.telegram_listener

    def _make_chat(self, deps: dict) -> TelegramChat:
        return TelegramChat(
                sender=deps['sender'],
                message=deps['raw_message'],
                function_sender=self._sender_func,
                logger=self.logger,
                message_id=deps['message_id'],
                username=deps['username'],
                fetch_async=self.fetch_async,
                error_message=self._chat_error_message,
                unknown_message=self._chat_unknown_message,
                refuse_message=self._chat_refuse_message,
            )

    async def _send_async(self, message: str, user: str | int) -> dict:
        result = {}
        for msg in wrap(message, 4096):
            send_data = {"chat_id": user, "text": msg}
            result = await self.fetch_async("sendMessage", send_data)
        return result

    async def fetch_async(
            self,
            method: str,
            data: dict,
            headers: dict | None = None,
            ignore_errors: bool = False,
            timeout: float = 30.,
    ) -> dict:
        url = f"https://api.telegram.org/bot{self.__token}/{method}"
        response = await self.__http_session.post(url=url, json=data, headers=headers, timeout=timeout)

        answer = response.json()

        if not answer["ok"] and not ignore_errors:
            state = await self._handle_error_async(answer)
            if state == 0:  # repeat request
                await asyncio.sleep(4)
                response = await self.__http_session.post(
                    url=url, json=data, headers=headers, timeout=timeout,
                )
                answer = response.json()
            if not answer["ok"]:
                raise RestartListeningException
        return answer

    async def telegram_listener(self) -> AsyncGenerator[dict, None]:
        if self.__first_time_launched and self.__greeting_enabled and self._admin is not None:
            await self._sender_func(f"{self.name} is started!", self._admin)

        async for update in self._get_updates_async():
            yield update

    def _configure_middlewares(self) -> None:
        self._middlewares = self._custom_middlewares or [
                process_listener_exceptions,
                execute_listener,
                deconstruct_telegram_message,
                process_handler_exceptions,
                load_dependencies,
                load_chat_dependencies,
                route_chat_message,
                *self._user_middlewares,
                call_with_dependencies_injected,
            ]

    async def _handle_server_connection_error_async(self) -> None:
        await self.logger.info_async(
            f"Connection ERROR in {self.name}. Sleep 5 seconds",
        )
        await asyncio.sleep(5)

    async def _get_updates_async(self) -> AsyncGenerator[dict, None]:
        """Long Polling: Telegram BOT API https://core.telegram.org/bots/api
        """
        timeout = 1000
        data = {"timeout": timeout, "limit": 1, "allowed_updates": self.ALLOWED_UPDATES}
        if self.__first_time_launched or self.__should_skip_old_updates:
            self.first_time_launched = False
            data["offset"] = await self._skip_old_updates_async()
        while True:
            try:
                ans = await self.fetch_async("getUpdates", data, ignore_errors=True, timeout=timeout*2)
            except httpx.ConnectError:
                await self._handle_server_connection_error_async()
                continue
            if not ans["ok"]:
                state = await self._handle_error_async(ans)
                if state == 0:
                    await asyncio.sleep(5)
                    continue
                else:
                    msg = f"Error {ans} while receiving long polling server"
                    raise ExitBotException(msg)
            if len(ans["result"]) != 0:
                data["offset"] = ans["result"][0]["update_id"] + 1
                yield ans

    async def _handle_error_async(self, error: dict) -> int:
        """https://core.telegram.org/api/errors
        :returns: whether code should continue executing after the error.
        -1 if bot should be exited. Raises BaseException this case
        0 if it should just repeat request.
        1 if it's better to finish this request. The same subsequent requests will fail too.
        """
        error_code: int = error["error_code"]
        error_msg: str = error["description"]
        msg = f"Error {error_code} from TG API: {error_msg}"
        # notify administrator and repeat request
        if error_code in (400, 403, 404, 406, 303) or 500 <= error_code <= 599:
            await self.logger.error_async(msg)
            return 1
        # too many requests (flood)
        if error_code == 420:
            await self.logger.error_async(
                f"{self.name} reached Flood error. Fix the code",
            )
            await asyncio.sleep(10)
            return 0
        # unauthorized
        if error_code == 401:
            await self.logger.critical_async(msg)
            raise ExitBotException
        if error_code == 409:
            msg = (
                "Error code 409. Another telegram instance is working. "
                "Shutting down this instance"
            )
            await self.logger.critical_async(msg)
            raise ExitBotException(msg)
        await self.logger.error_async("Unknown error. Add code " + msg)
        return 1

    async def _skip_old_updates_async(self) -> int:
        data = {"timeout": 0, "limit": 1, "offset": -1}
        ans = await self.fetch_async("getUpdates", data)
        result = ans["result"]
        if len(result) > 0:
            return result[0]["update_id"] + 1
        return -1

    async def before_close_async(self) -> None:
        await super().before_close_async()
        if not self.__http_session.is_closed:
            await self.__http_session.aclose()

    async def before_start_async(self) -> None:
        await super().before_start_async()
        self.__http_session = httpx.AsyncClient()


def build_task_caller(info: TaskInfo, bot: Bot) -> Callable[..., Any]:
    func = info.func

    async def caller() -> Any:
        try:
            if bot.is_enabled:
                min_deps = decompose_bot_as_dependencies(bot)
                args = resolve_function_args(func, min_deps)
                return await func(**args)
        except (AttributeError, TypeError, KeyError, AssertionError) as e:
            await bot.logger.critical_async(
                f"Fix the code. Critical `{e.__class__.__name__}` "
                f"raised:\n{e}.\nFull traceback:\n{format_exc()}",
            )
        except Exception as e:
            await bot.logger.exception_async(
                f"Bot {bot.name} was raised with unhandled `{e.__class__.__name__}` "
                f"and kept on working:\n{e}.\nFull traceback:\n{format_exc()}",
            )
        else:
            return None

    def wrapped_caller() -> Any:
        return caller()

    return wrapped_caller


def build_scheduler(bots: list[Bot], scheduler: IScheduler) -> None:
    task_names = set()
    for bot in bots:
        for task_info in bot.task_infos:
            assert task_info.name not in task_names, f'Task {task_info.name} met twice. Tasks must have different names'
            task_names.add(task_info.name)
            scheduler.add_task(task_info, build_task_caller(task_info, bot))
    task_names.clear()


def disable_tasks(bot: Bot, scheduler: IScheduler) -> None:
    """Method is used to disable tasks when the bot is exiting or disabling."""
    scheduled_tasks = scheduler.list_tasks()
    for bot_task in (ti.name for ti in bot.task_infos):
        if bot_task in scheduled_tasks:
            scheduler.remove_task(bot_task)


async def stop_bot_async(bot: Bot, scheduler: IScheduler) -> None:
    bot.disable()
    disable_tasks(bot, scheduler)

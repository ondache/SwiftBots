from swiftbots import Bot
from swiftbots.middlewares import process_listener_exceptions, process_handler_exceptions


class CloseTestAppException(BaseException): ...


exceptions_handler_middlewares = {
    process_handler_exceptions,
    process_listener_exceptions
}


def close_test_app():
    raise CloseTestAppException()


def run_raisable(app):
    try:
        app.run()
    except CloseTestAppException:
        ...


def extract_exception_handler_middlewares(bot: Bot) -> None:
    middlewares = bot._middlewares
    middlewares = list(filter(lambda m: m not in exceptions_handler_middlewares, middlewares))
    bot._middlewares = middlewares

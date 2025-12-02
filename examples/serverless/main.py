import os

from swiftbots import SwiftBots, TelegramBot
from swiftbots.all_types import ILogger
from swiftbots.runners import run_oneshot
from swiftbots.middlewares import (
    call_with_dependencies_injected,
    route_chat_message,
    load_dependencies,
    load_chat_dependencies,
    deconstruct_telegram_message,
)
import azure.functions as func

# Pass your token and admin id!
token = os.environ.get('TOKEN')
assert token, 'Missing environment variable "TOKEN"'
admin = os.environ.get('ADMIN')

# Bot configuration
bot = TelegramBot(
    token,
    admin,
    name='My Bot',
    middlewares=[
        deconstruct_telegram_message,
        load_dependencies,
        load_chat_dependencies,
        route_chat_message,
        call_with_dependencies_injected,
    ],
)


# Define handlers
@bot.message_handler(commands=['add', '+'])
async def add(message: str, logger: ILogger, chat: bot.Chat):
    await logger.debug_async(f'User is requesting ADD operation: {message}')
    num1, num2 = map(float, message.split(' '))
    result = num1 + num2
    await chat.reply_async(f'Hello, {chat.username}!')
    await chat.reply_async(f'The result is: {result}')


@bot.message_handler(commands=['sub', '-'])
async def subtract(message: str, logger: ILogger, chat: bot.Chat):
    await logger.debug_async(f'User is requesting SUBTRACT operation: {message}')
    num1, num2 = map(float, message.split(' '))
    result = num1 - num2
    await chat.reply_async(f'Hello, {chat.username}!')
    await chat.reply_async(f'The result is: {result}')


@bot.default_handler()
async def default_handler(message: str, logger: ILogger, chat: bot.Chat):
    await logger.debug_async(f'User is requesting default handler: {message}')
    await chat.reply_async(f'[default handler] Unknown command: {message}')


# Configure and run the app
swiftbots_app = SwiftBots(runner=run_oneshot)

swiftbots_app.add_bot(bot)

# Configure Azure Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="azure_trigger", auth_level=func.AuthLevel.FUNCTION)
def azure_trigger(req: func.HttpRequest) -> func.HttpResponse:
    swiftbots_app.run(
        scheduler_enabled=False,
        run_with=req.get_json()
    )
    return func.HttpResponse(status_code=200)

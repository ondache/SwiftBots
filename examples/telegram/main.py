import os

from swiftbots import SwiftBots, TelegramBot
from swiftbots.admin_utils import send_telegram_message, send_telegram_message_async
from swiftbots.all_types import ILogger
from swiftbots.loggers import AdminLoggerFactory

# Pass your token and admin id!
token = os.environ.get('TOKEN')
assert token, 'Missing environment variable "TOKEN"'
admin = os.environ.get('ADMIN')

# Logging configuration. The admin will receive error reports instantly
tg_admin_logger_factory = None
if admin:
    def report_func(msg):
        send_telegram_message(msg, admin, token)


    async def report_async_func(msg):
        await send_telegram_message_async(msg, admin, token)


    tg_admin_logger_factory = AdminLoggerFactory(report_func, report_async_func)


# Bot configuration
bot = TelegramBot(token, admin, name='My Bot', bot_logger_factory=tg_admin_logger_factory)


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
app = SwiftBots()

app.add_bots([bot])

app.run()

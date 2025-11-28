from swiftbots import ChatBot
from swiftbots.admin_utils import get_bot_names_async, shutdown_app, shutdown_bot_async, start_bot_async

bot = ChatBot(name='admin_bot')


@bot.sender()
async def send_async(message, user):
    print(message)


@bot.listener()
async def listen():
    print('Welcome to the admin bot!')
    print('Input a command (list, start <bot>, stop <bot>):')
    while True:
        message = input('-> ')
        yield {
            'message': message,
            'sender': 'User'
        }


@bot.message_handler(commands=['list'])
async def list_endpoint(chat: bot.Chat):
    all_bots, running, stopped = map(', '.join, await get_bot_names_async())

    message = f'All bots:\n- {all_bots}\n' if all_bots else 'No tasks\n'
    message += f"Running bots:\n- {running}\n" if running else 'No running tasks\n'
    message += f"Stopped tasks:\n- {stopped}" if stopped else 'No stopped tasks'

    await chat.reply_async(message)


@bot.message_handler(commands=['stop'])
async def stop_endpoint(chat: bot.Chat, arguments: str):
    bot_to_exit = arguments.strip()
    if not bot_to_exit:
        shutdown_app()
        return

    result = await shutdown_bot_async(bot_to_exit)
    if result:
        await chat.reply_async(f'Bot {bot_to_exit} was stopped')
    else:
        await chat.reply_async(f'Bot {bot_to_exit} was not found')


@bot.message_handler(commands=['start'])
async def start_endpoint(chat: bot.Chat, arguments: str):
    bot_to_start = arguments.strip()
    if not bot_to_start:
        await chat.reply_async('You have to pass a name of the bot to start')
        return

    result = await start_bot_async(bot_to_start)
    if result == 1:
        await chat.reply_async(f'Bot {bot_to_start} is already running')
    elif result == 2:
        await chat.reply_async(f'Bot {bot_to_start} was not found')

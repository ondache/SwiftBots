import asyncio

from swiftbots import ChatBot, SwiftBots


def input_async(*args, **kwargs):
    return asyncio.to_thread(input, *args, **kwargs)


bot = ChatBot()


@bot.listener()
async def listen():
    print("Welcome in the command line chat! Good day, Friend!")
    print("Type expression to solve like `+ 2 2` or `- 70 1`")
    while True:
        message = await input_async('-> ')
        yield {
            'message': message,
            'sender': 'User'
        }


@bot.sender()
async def send_async(message, user):
    print(message)


@bot.message_handler(commands=['+', 'add'])
async def add(message: str, chat: bot.Chat):
    try:
        num1, num2 = map(float, message.split(' '))
    except ValueError:
        await chat.reply_async('Invalid input. The format: `+ <number> <number>`')
        return
    result = num1 + num2
    await chat.reply_async(str(result))


@bot.message_handler(commands=['-', 'sub'])
async def subtract(message: str, chat: bot.Chat):
    try:
        num1, num2 = map(float, message.split(' '))
    except ValueError:
        await chat.reply_async('Invalid input. The format: `- <number> <number>`')
        return
    result = num1 - num2
    await chat.reply_async(str(result))


@bot.default_handler()
async def default_handler(message: str, chat: bot.Chat):
    await chat.reply_async(f'[default handler] Unknown command: {message}')


app = SwiftBots()

app.add_bots([bot])

app.run()

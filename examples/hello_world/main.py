from swiftbots import Bot, SwiftBots

app = SwiftBots()

bot = Bot()


@bot.listener()
async def listen():
    print('Welcome to the console bot! Type anything and press enter:')
    while True:
        message = input('-> ')
        yield {
            'message': message
        }


@bot.handler()
async def handle(message: str):
    print(f'Received message: {message}')


app.add_bots([bot])

app.run()

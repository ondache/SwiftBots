import asyncio
import random

from swiftbots import ChatBot, PeriodTrigger, SwiftBots
from swiftbots.admin_utils import shutdown_app


def input_async(*args, **kwargs):
    return asyncio.to_thread(input, *args, **kwargs)


app = SwiftBots()

bot = ChatBot()


db = {
    'facts': [
        'Octopuses have three hearts.',
        'The plastic or metal tip of your shoelace is called an aglet.',
        'Cats sleep an average of 15 hours per day.',
        'The femur is the longest bone in the human body.',
        'Baby hedgehogs are called hoglets.',
        'Bats are the only flying mammals.',
        'A watermelon is 92% water.',
    ],
    'weather':[
        'Beijing +18°C, wind 8 km/h, humidity 50%',
        'Lisbon +14°C, wind 16 km/h, humidity 66%',
        'Montevideo +16°C, wind 13 km/h, humidity 69%'
    ]
}


@bot.listener()
async def listen():
    print('Welcome to the console bot! You can type `exit`, `list`, `start <task>` or `stop <task>` and press enter:')
    while True:
        message = await input_async('-> ')
        yield {
            'message': message,
            'sender': 'User'
        }


@bot.sender()
async def send_async(message, user):
    print(message)


# Handlers
@bot.message_handler(commands=['exit'])
async def exit_app():
    print('Exiting...')
    shutdown_app()


@bot.default_handler()
async def default_handler(message: str):
    print(f'Message received: {message}')


# Tasks
@bot.task(PeriodTrigger(seconds=4), run_at_start=True, name='facts')
async def fun_facts_task():
    facts_db = db['facts']
    idx = random.randint(0, len(facts_db) - 1)
    print(f'Fact #{idx+1}: {facts_db[idx]}', end='\n-> ')


@bot.task(PeriodTrigger(seconds=7), name='weather')
async def weather_task():
    weather_db = db['weather']
    idx = random.randint(0, len(weather_db) - 1)
    print(f'Weather report for {weather_db[idx]}', end='\n-> ')

app.add_bots([bot])

app.run()

import admin_bot

from swiftbots import StubBot, SwiftBots

app = SwiftBots()

app.add_bots([
    admin_bot.bot,
    StubBot(name='bot1'),
    StubBot(name='bot2')
])

app.run()

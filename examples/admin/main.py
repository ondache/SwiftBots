from swiftbots import SwiftBots, StubBot

import admin_bot


app = SwiftBots()

app.add_bots([
    admin_bot.bot,
    StubBot(name='bot1'),
    StubBot(name='bot2')
])

app.run()

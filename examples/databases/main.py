import logging

from swiftbots import SwiftBots

from notes_bot import bot

# just to not spam
logging.basicConfig(level=logging.ERROR)

app = SwiftBots()

app.add_bots([bot])

app.run()

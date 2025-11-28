import logging

from notes_bot import bot

from swiftbots import SwiftBots

# just to not spam
logging.basicConfig(level=logging.ERROR)

app = SwiftBots()

app.add_bots([bot])

app.run()

import re
import asyncio
from datetime import datetime as dt, timezone

from swiftbots import ChatBot, depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from database.database import create_session_async
from models.notes import Note


NAME_TEXT_PATTERN = re.compile(r'^(\S+)\s+(\S+.*)$', re.IGNORECASE | re.DOTALL)


def input_async(*args, **kwargs):
    return asyncio.to_thread(input, *args, **kwargs)

bot = ChatBot()


@bot.listener()
async def listen():
    print("Welcome in the command line chat! Good day, Friend!")
    while True:
        message = await input_async('-> ')
        yield {
            'message': message,
            'sender': 'User'
        }


@bot.sender()
async def send_async(message, user):
    print(message)


@bot.message_handler(commands=['+note', 'add note'])
async def create(chat: bot.Chat, message: str, session: AsyncSession = depends(create_session_async)):
    match = NAME_TEXT_PATTERN.match(message)

    if not match:
        await chat.reply_async("There are no name or text of a new note. "
                               "Use the command like '+note <note_name> <text_of_note>'")
        return

    name = match.group(1)
    text = match.group(2)

    async with session:
        note = await session.scalar(select(Note)
                                    .where(Note.name == name))

        # Note already exists
        if note is not None:
            await chat.reply_async(f"Note '{name}' already exists. And it's overwritten. "
                                   f"Its previous text is:\n{note.text}")
            note.text = text
            note.modified = dt.now(tz=timezone.utc)

        # Note doesn't exist
        else:
            session.add(Note(name=name, text=text))

        await session.commit()
        await chat.reply_async("Notes updated")


@bot.message_handler(commands=['note'])
async def read(message: str, chat: bot.Chat, session: AsyncSession = depends(create_session_async)):
    name = message.strip()
    if not name:
        await chat.reply_async("No note name given")

    async with session:
        note = await session.scalar(select(Note)
                                    .where(Note.name == name))

        if note is None:
            await chat.reply_async("There's no note with such name")
            return
        await chat.reply_async(note.text)


@bot.message_handler(commands=['++note', 'update note'])
async def update(message: str, chat: bot.Chat, session: AsyncSession = depends(create_session_async)):
    match = NAME_TEXT_PATTERN.match(message)

    if not match:
        await chat.reply_async("There are no name or text of new note. "
                               "Use the command like '++note <note_name> <text_to_add>'")
        return

    name = match.group(1)
    text = match.group(2)

    async with session:
        note = await session.scalar(select(Note)
                                    .where(Note.name == name))

        # Note doesn't exist
        if note is None:
            await chat.reply_async("There's no such note")
            return

        # Note exists
        note.text += '\n' + text
        note.modified = dt.utcnow()
        await session.commit()
        await chat.reply_async("Notes updated")


@bot.message_handler(commands=['-note', 'delete note', 'remove note'])
async def delete(message: str, chat: bot.Chat, session: AsyncSession = depends(create_session_async)):
    name = message

    async with session:
        note = await session.scalar(select(Note)
                                    .where(Note.name == name))

        # Note doesn't exist
        if note is None:
            await chat.reply_async("There's no such note")
            return

        # Note exists
        await session.delete(note)
        await session.commit()
        await chat.reply_async("Notes updated")


@bot.message_handler(commands=['notes'])
async def list_notes(chat: bot.Chat, session: AsyncSession = depends(create_session_async)):
    async with session:
        notes = (await session.scalars(select(Note.name)
                                       .order_by(Note.modified))).all()

        if len(notes) == 0:
            await chat.reply_async("No notes")
        else:
            msg = '\n'.join(notes)
            await chat.reply_async(msg)

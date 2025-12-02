from textwrap import wrap
from collections.abc import Callable

from swiftbots.all_types import ILogger
from swiftbots.types import AsyncSenderFunction


class Chat:
    def __init__(
            self,
            sender: str | int,
            message: str,
            function_sender: AsyncSenderFunction,
            logger: ILogger,
            error_message: str,
            unknown_message: str,
            refuse_message: str,
    ):
        self.sender = sender
        self.message = message
        self.function_sender = function_sender
        self.logger = logger
        self.error_message = error_message
        self.unknown_message = unknown_message
        self.refuse_message = refuse_message

    async def reply_async(self, message: str) -> dict:
        """Send the user the message back.
        """
        return await self.function_sender(message, self.sender)

    async def error_async(self) -> dict:
        """Inform the user there is an internal error.
        """
        await self.logger.error_async(f"Error in the bot. The sender: {self.sender}, the message: {self.message}")
        return await self.reply_async(self.error_message)

    async def unknown_command_async(self) -> dict:
        """If the user sends some unknown shit, then needed to warn him
        """
        await self.logger.info_async(f"{self.sender} sent unknown command. {self.message}")
        return await self.reply_async(self.unknown_message)

    async def refuse_async(self) -> dict:
        """If the user can't use it, then he must be aware.
        """
        await self.logger.info_async(f"Forbidden. The sender: {self.sender}, the message: {self.message}")
        return await self.reply_async(self.refuse_message)


class TelegramChat(Chat):
    def __init__(
            self,
            sender: str | int,
            message: str,
            function_sender: AsyncSenderFunction,
            logger: ILogger,
            message_id: int,
            username: str | None,
            fetch_async: Callable,
            error_message: str,
            unknown_message: str,
            refuse_message: str,
    ):
        super().__init__(sender=sender,
                         message=message,
                         function_sender=function_sender,
                         logger=logger,
                         error_message=error_message,
                         unknown_message=unknown_message,
                         refuse_message=refuse_message)
        self.message_id = message_id
        self.username = username
        self.fetch_async = fetch_async

    async def update_message_async(
        self, new_text: str, message_id: int, data: dict | None = None,
    ) -> dict:
        if data is None:
            data = {}
        data["text"] = new_text
        data["message_id"] = message_id
        data["chat_id"] = self.sender
        return await self.fetch_async("editMessageText", data)

    async def send_async(
        self, message: str, user: str | int, data: dict | None = None,
    ) -> dict:
        if data is None:
            data = {}

        messages = wrap(
                message,
                4096,
                expand_tabs=True,
                replace_whitespace=True,
                fix_sentence_endings=False,
                break_long_words=True,
                break_on_hyphens=True,
                drop_whitespace=True,
        )
        result = {}
        for msg in messages:
            send_data = {"chat_id": user, "text": msg}
            send_data.update(data)
            result = await self.fetch_async("sendMessage", send_data)
        return result

    async def delete_message_async(
        self, message_id: int, data: dict | None = None,
    ) -> dict:
        if data is None:
            data = {}
        data["chat_id"] = self.sender
        data["message_id"] = message_id
        return await self.fetch_async("deleteMessage", data)

    async def send_sticker_async(
        self, file_id: str, data: dict | None = None,
    ) -> dict:
        if data is None:
            data = {}
        data["chat_id"] = self.sender
        data["sticker"] = file_id
        return await self.fetch_async("sendSticker", data)

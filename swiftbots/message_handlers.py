import re
from typing import Union

from swiftbots.c_ext import search_ext
from swiftbots.types import DecoratedCallable

FINAL_INDICATOR = '**'


class CompiledChatCommand:
    def __init__(
        self,
        command_name: str,
        method: DecoratedCallable,
        pattern: re.Pattern,
        whitelist_users: list[str] | None,
        blacklist_users: list[str] | None,
    ):
        self.command_name = command_name
        self.method = method
        self.pattern = pattern
        self.whitelist_users = whitelist_users
        self.blacklist_users = blacklist_users


Trie = dict[str, Union["Trie", "CompiledChatCommand"]]


def insert_trie(trie: Trie, word: str, command: CompiledChatCommand) -> None:
    for ch in word:
        trie = trie.setdefault(ch, {})
    trie[FINAL_INDICATOR] = command


def search_best_command_match(trie: Trie, word: str) -> tuple[CompiledChatCommand | None, re.Match | None]:
    matches = [trie[FINAL_INDICATOR]] if FINAL_INDICATOR in trie else []
    sub_word = word
    while trie is not None:
        trie = search_ext.search_trie(trie, sub_word.lower())
        if trie is not None:
            command: CompiledChatCommand = trie[FINAL_INDICATOR]
            matches.append(command)
            sub_word = word[len(command.command_name):]
    for command in reversed(matches):
        match = command.pattern.fullmatch(word)
        if match is not None:
            return command, match
    return None, None


class ChatMessageHandler:
    def __init__(self,
                 commands: list[str],
                 function: DecoratedCallable,
                 whitelist_users: list[str | int] | None,
                 blacklist_users: list[str | int] | None):
        self.commands = commands
        self.function = function
        self.whitelist_users = None if whitelist_users is None else [str(x).casefold() for x in whitelist_users]
        self.blacklist_users = None if blacklist_users is None else [str(x).casefold() for x in blacklist_users]


def compile_command_as_regex(name: str) -> re.Pattern:
    """Compile with regex patterns all the command names for the faster search.
    Pattern is:
    1. Begins with the NAME OF COMMAND (case-insensitive).
    2. Then any whitespace characters [ \f\n\r\t\v] (zero or more).
    3. Then the rest of the text (let's name it arguments). Marks as group 1.
    Group 1 is optional. If there is empty group 1, then the message is entirely match the command
    """
    if len(name) == 0:
        return re.compile(r"^(.*)$", re.DOTALL)
    escaped_name = re.escape(name)
    return re.compile(rf"^{escaped_name}(?:\s+(.*))?$", re.IGNORECASE | re.DOTALL)


def compile_chat_commands(
    handlers: list[ChatMessageHandler],
) -> list[CompiledChatCommand]:
    return [
        CompiledChatCommand(
            command_name=command,
            method=handler.function,
            pattern=compile_command_as_regex(command),
            blacklist_users=handler.blacklist_users,
            whitelist_users=handler.whitelist_users,
        )
        for handler in handlers
        for command in handler.commands
    ]


def is_user_allowed(user: str | int,
                    whitelist_users: list[str] | None,
                    blacklist_users: list[str] | None,
                    ) -> bool:
    user = str(user).casefold()
    if blacklist_users is not None:
        return user not in blacklist_users
    if whitelist_users is not None:
        return user in whitelist_users
    return True

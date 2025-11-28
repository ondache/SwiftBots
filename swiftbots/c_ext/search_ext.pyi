from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiftbots.message_handlers import Trie


def search_trie(trie: Trie, word: str) -> Trie | None: ...

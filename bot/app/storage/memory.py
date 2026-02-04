from __future__ import annotations

class MemoryStore:
    def __init__(self) -> None:
        self._task_by_chat: dict[str, str] = {}

    def set_task(self, chat_id: str, task_id: str) -> None:
        self._task_by_chat[chat_id] = task_id

    def get_task(self, chat_id: str) -> str | None:
        return self._task_by_chat.get(chat_id)

    def clear_task(self, chat_id: str) -> None:
        self._task_by_chat.pop(chat_id, None)

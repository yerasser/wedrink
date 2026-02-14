import json
import logging
import os
from typing import Dict, Optional

from config import TOKENS_PATH

log = logging.getLogger(__name__)


class TokenStore:
    def __init__(self, path: str = TOKENS_PATH) -> None:
        self._path = path
        self._tokens: Dict[int, str] = {}
        self._load()

    # ── public API ────────────────────────────────────────────────────────────

    def get(self, tg_user_id: int) -> Optional[str]:
        return self._tokens.get(tg_user_id)

    def set(self, tg_user_id: int, token: str) -> None:
        self._tokens[tg_user_id] = token
        self._save()

    def drop(self, tg_user_id: int) -> None:
        self._tokens.pop(tg_user_id, None)
        self._save()

    # ── persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # ключи в JSON всегда строки — конвертируем в int
            self._tokens = {int(k): v for k, v in raw.items()}
            log.info("TokenStore: loaded %d tokens from %s", len(self._tokens), self._path)
        except Exception as e:
            log.warning("TokenStore: failed to load %s: %s", self._path, e)

    def _save(self) -> None:
        try:
            tmp = self._path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({str(k): v for k, v in self._tokens.items()}, f, ensure_ascii=False)
            os.replace(tmp, self._path)
        except Exception as e:
            log.error("TokenStore: failed to save %s: %s", self._path, e)
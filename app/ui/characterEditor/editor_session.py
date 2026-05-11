# app/ui/editor_session.py

from pathlib import Path
import json
from app.domain.character import Character


class EditorSession:
    """
    角色编辑会话状态（UI 无关）
    """

    AUTOSAVE_PATH = Path("app/drafts/character_editor_autosave.json")

    def __init__(self):
        self.character: Character = Character()
        self.current_path: str | None = None

        self._baseline_snapshot: dict = {}
        self._dirty: bool = False

    # ==========================
    # state
    # ==========================

    def load_character(self, c: Character, json_path: str | None = None):
        self.character = c
        self.current_path = json_path
        self._baseline_snapshot = self._make_snapshot()
        self._dirty = False

    def mark_dirty_if_needed(self, new_snapshot: dict):
        if new_snapshot != self._baseline_snapshot:
            self._dirty = True

    def reset_dirty(self):
        self._baseline_snapshot = self._make_snapshot()
        self._dirty = False

    def is_dirty(self) -> bool:
        return self._dirty

    # ==========================
    # snapshot
    # ==========================

    def _make_snapshot(self) -> dict:
        c = self.character
        return {
            **c.to_dict(),
            "image": c.image or None,
            "stories": c.stories or [],
        }

    # ==========================
    # autosave
    # ==========================

    def autosave(self):
        if not self._dirty:
            return

        self.AUTOSAVE_PATH.parent.mkdir(parents=True, exist_ok=True)

        data = self.character.to_dict()
        data["_type"] = "autosave"
        data["source"] = "autosave"

        with open(self.AUTOSAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def clear_autosave(self):
        if self.AUTOSAVE_PATH.exists():
            self.AUTOSAVE_PATH.unlink()

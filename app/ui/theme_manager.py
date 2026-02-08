from pathlib import Path
from PyQt6.QtWidgets import QApplication
import json


class ThemeManager:

    THEME_DIR = Path("app/assets/themes")
    CONFIG = Path("app/theme.json")

    current = "yuri"

    @classmethod
    def available(cls):
        return [p.stem for p in cls.THEME_DIR.glob("*.qss")]

    @classmethod
    def load(cls):
        if cls.CONFIG.exists():
            try:
                cls.current = json.loads(cls.CONFIG.read_text()).get("theme", "yuri")
            except Exception:
                pass

    @classmethod
    def save(cls):
        cls.CONFIG.write_text(
            json.dumps({"theme": cls.current}, indent=2),
            encoding="utf-8"
        )

    @classmethod
    def apply(cls, name: str):
        path = cls.THEME_DIR / f"{name}.qss"
        if not path.exists():
            return

        qss = path.read_text(encoding="utf-8")

        QApplication.instance().setStyleSheet(qss)

        cls.current = name
        cls.save()

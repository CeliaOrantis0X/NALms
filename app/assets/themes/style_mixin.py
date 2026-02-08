# app/ui/config/style_mixin.py
from pathlib import Path

class BaseStyleMixin:
    def load_base_style(self):
        qss = Path("app/config/base.qss")
        if qss.exists():
            self.setStyleSheet(qss.read_text(encoding="utf-8"))

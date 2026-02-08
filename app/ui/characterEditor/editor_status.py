# app/ui/editor_status.py

from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import QTimer, Qt
from datetime import datetime
from pathlib import Path


class EditorStatus(QWidget):
    """
    编辑器状态栏（轻量）
    """

    def __init__(self, parent=None, timeout_ms: int = 5000):
        super().__init__(parent)

        self._timeout_ms = timeout_ms

        self.label = QLabel("Ready")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label.setStyleSheet(
            "color:#666; padding:4px 8px; font-size:12px;"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._clear)

    # -------------------------
    # public API
    # -------------------------

    def info(self, text: str):
        self._show(text, "#666")

    def success(self, text: str):
        self._show(text, "#2e7d32")

    def warning(self, text: str):
        self._show(text, "#b26a00")

    def error(self, text: str):
        self._show(text, "#c62828")

    # -------------------------
    # helpers
    # -------------------------

    def _show(self, text: str, color: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.label.setText(f"[{timestamp}] {text}")
        self.label.setStyleSheet(
            f"color:{color}; padding:4px 8px; font-size:12px;"
        )
        self._timer.start(self._timeout_ms)

    def _clear(self):
        self.label.setText("Ready")
        self.label.setStyleSheet(
            "color:#999; padding:4px 8px; font-size:12px;"
        )

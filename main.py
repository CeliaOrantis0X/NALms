import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from app.ui.main_window import MainWindow
from app.ui.theme_manager import ThemeManager


QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)


def main():
    app = QApplication(sys.argv)

    ThemeManager.load()
    ThemeManager.apply(ThemeManager.current)

    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

project_root = Path(__file__).parent

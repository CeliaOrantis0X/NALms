import logging
import sys
import traceback
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from app.ui.main_window import MainWindow
from app.ui.theme_manager import ThemeManager

project_root = Path(__file__).parent
LOG_PATH = project_root / "nalms.log"   # *.log 已在 .gitignore 中

QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)


def install_excepthook():
    """
    PyQt6 中，槽函数里未捕获的异常默认会直接终止整个进程。
    装上钩子后：写日志 + 弹窗提示，程序继续运行。
    """
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.ERROR,
        encoding="utf-8",
        format="%(asctime)s %(levelname)s %(message)s",
    )

    def hook(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return

        text = "".join(traceback.format_exception(exc_type, exc, tb))

        try:
            logging.error("Unhandled exception:\n%s", text)
            if sys.stderr:
                sys.stderr.write(text)
            if QApplication.instance() is not None:
                QMessageBox.critical(
                    None,
                    "Unexpected Error",
                    f"{exc_type.__name__}: {exc}\n\nDetails were written to:\n{LOG_PATH}",
                )
        except Exception:
            pass   # 钩子本身绝不能再抛异常

    sys.excepthook = hook


def main():
    app = QApplication(sys.argv)

    install_excepthook()

    ThemeManager.load()
    ThemeManager.apply(ThemeManager.current)

    win = MainWindow()
    win.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

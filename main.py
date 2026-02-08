import sys

from PyQt6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.ui.theme_manager import ThemeManager

from pathlib import Path
from app.tuils import check_project_structure

app = QApplication(sys.argv)

ThemeManager.load()
ThemeManager.apply(ThemeManager.current)

'''
qss_path = Path("app/assets/themes/base_yuri.qss")
if qss_path.exists():
    app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
'''

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

project_root = Path(__file__).parent
issues = check_project_structure(project_root)

for issue in issues:
    print(issue)
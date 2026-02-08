# app/ui/styles.py

DARK_THEME = """
QWidget {
    background-color: #1e1e1e;
    color: #dddddd;
    font-family: "Segoe UI", "Microsoft YaHei";
    font-size: 12px;
}

QLabel {
    color: #dddddd;
}

QPushButton {
    background-color: #2d2d30;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    padding: 6px 14px;
    color: #ffffff;
}

QPushButton:hover {
    background-color: #3a3a3d;
}

QPushButton:pressed {
    background-color: #007acc;
}

QComboBox, QSpinBox {
    background-color: #2d2d30;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    padding: 4px 8px;
}

QScrollArea {
    border: none;
}

QScrollBar:vertical {
    background: #1e1e1e;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: #3c3c3c;
    border-radius: 5px;
}
"""

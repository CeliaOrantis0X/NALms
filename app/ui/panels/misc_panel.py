# app/ui/characterEditor/panels/misc_panel.py

from PyQt6.QtWidgets import (
    QGroupBox,
    QGridLayout,
    QLabel,
    QLineEdit
)


def build_misc_panel(editor):

    g = QGroupBox("Misc")
    l = QGridLayout(g)

    editor.tag_input = QLineEdit()
    editor.partnership_input = QLineEdit()
    editor.media_input = QLineEdit()

    for w in (
        editor.tag_input,
        editor.partnership_input,
        editor.media_input
    ):
        w.setProperty("class", "fieldInput")

    fields = [
        ("Media", editor.media_input),
        ("Partnership", editor.partnership_input),
        ("Tags", editor.tag_input),
    ]

    for i, (label, widget) in enumerate(fields):

        lab = QLabel(label)
        lab.setProperty("class", "fieldLabel")

        row = i // 2
        col = (i % 2) * 2

        l.addWidget(lab, row, col)
        l.addWidget(widget, row, col + 1)

    return g
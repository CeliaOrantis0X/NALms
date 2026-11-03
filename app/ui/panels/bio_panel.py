# app/ui/panels/bio_panel.py

from PyQt6.QtWidgets import (
    QGroupBox,
    QGridLayout,
    QLabel,
    QComboBox
)

from app.ui.characterEditor.field_schema import BIO_FIELDS


def build_bio_panel(editor):

    g = QGroupBox("Biography")
    l = QGridLayout(g)

    fields = []

    for field in BIO_FIELDS:

        widget = editor._create_widget_from_schema(field)

        setattr(
            editor,
            f'{field["key"]}_input',
            widget
        )

        if field["key"] == "gender":
            editor.gender_cb = widget

        fields.append(
            (field["label"], widget)
        )

    for i, (label, widget) in enumerate(fields):

        r = i // 2
        c = (i % 2) * 2

        lab = QLabel(label)
        lab.setProperty("class", "fieldLabel")

        l.addWidget(lab, r, c)
        l.addWidget(widget, r, c + 1)

    return g
# app/ui/panels/profile_panel.py

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QComboBox
)

from PyQt6.QtCore import Qt


def build_profile_card(editor):

    card = QWidget()
    card.setProperty("class", "card")
    card.setFixedWidth(300)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(10)

    # =================
    # Avatar
    # =================

    editor.avatar = QLabel("No Image\nClick Import")
    editor.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
    editor.avatar.setObjectName("Avatar")
    editor.avatar.setFixedHeight(300)

    import_btn = QPushButton("Import Image")
    import_btn.clicked.connect(editor._import_image)
    import_btn.setFixedHeight(28)

    layout.addWidget(editor.avatar)
    layout.addWidget(import_btn)

    # =================
    # Divider
    # =================

    divider = QFrame()
    divider.setFrameShape(QFrame.Shape.HLine)
    divider.setProperty("class", "softDivider")

    layout.addWidget(divider)

    # =================
    # Ratings
    # =================

    title = QLabel("Ratings")
    title.setProperty("class", "sectionTitle")
    layout.addWidget(title)

    grid = QGridLayout()
    grid.setHorizontalSpacing(8)
    grid.setVerticalSpacing(6)

    editor.charm_cb = QComboBox()
    editor.charm_cb.addItems([
        "", "SSS+", "SSS", "SS", "S", "A"
    ])

    editor.capability_cb = QComboBox()
    editor.capability_cb.addItems([
        "", "Lv6", "Lv5", "Lv4",
        "Lv3", "Lv2", "Lv1", "Lv0"
    ])

    for w in (
        editor.charm_cb,
        editor.capability_cb
    ):
        w.setProperty("class", "fieldInput")

    fields = [
        ("Charm", editor.charm_cb),
        ("Capability", editor.capability_cb),
    ]

    for i, (label, widget) in enumerate(fields):

        r = i // 2
        c = (i % 2) * 2

        lab = QLabel(label)
        lab.setProperty("class", "fieldLabel")

        grid.addWidget(lab, r, c)
        grid.addWidget(widget, r, c + 1)

    layout.addLayout(grid)
    layout.addStretch()

    return card
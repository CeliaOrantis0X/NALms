# app/ui/dialog.py
# CharacterReaderDialog — Reworked Reader Layout
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QTextEdit, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QFrame, QWidget,
    QGridLayout, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from app.ui.characterEditor.editor import CharacterEditorDialog
from app.ui.panels.xfile_reader import XFileArchiveReader
# from app.config.style_mixin import BaseStyleMixin


class CharacterReaderDialog(QDialog):

    READER_BTN_ACTIVE = """
    QPushButton {
        background-color: #e6d9f5;
        color: #5a3b6e;
        font-weight: bold;
        border-radius: 10px;
        padding: 6px 14px;
        border: 1px solid #d2bfe8;
    }

    QPushButton:hover {
        background-color: #f0e6fb;
    }
    """

    READER_BTN_INACTIVE = """
        QPushButton {
        background-color: rgba(255,255,255,0.6);
        color: #8a6fa3;
        border-radius: 10px;
        padding: 6px 14px;
        border: 1px solid #e2d6f0;
    }

    QPushButton:hover {
        background-color: #f6effc;
        color: #5a3b6e;
        }
    """

    def __init__(self, character, json_path: str | None = None, parent=None):
        super().__init__(parent)
        # self.load_base_style()
        
        self.character = character
        self.json_path = json_path
        self._editor_saved_path = None

        self.setWindowTitle(character.name or "Character Reader")
        self.resize(980, 760)

        root = QHBoxLayout(self)
        root.setSpacing(14)

        # ======================
        # meta area (left)
        # ======================
        root.addWidget(self._build_left_panel(), 0)

        # ======================
        # Content Area (Right)
        # ======================
        # root.addWidget(self._build_right_panel(), 1)
        root.addLayout(self._build_content_area())

    # --------------------------------------------------
    # Left Panel (Image + Fields + Actions)
    # --------------------------------------------------
    def _build_left_panel(self):
        # ===== Card Root =====
        card = QWidget()
        card.setProperty("class", "card")
        card.setFixedWidth(300)

        outer = QVBoxLayout(card)
        outer.setContentsMargins(14, 14, 14, 12)
        outer.setSpacing(10)

        # ------------------------------------------------
        # Avatar
        # ------------------------------------------------

        avatar = QLabel()
        avatar.setObjectName("Avatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedHeight(300)

        if self.character.image:
            img_path = Path(self.character.image)
            if img_path.exists():
                pix = QPixmap(str(img_path))
                if not pix.isNull():
                    avatar.setPixmap(
                        pix.scaledToHeight(
                            280,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    )

        outer.addWidget(avatar)

        # ------------------------------------------------
        # Name / Alias
        # ------------------------------------------------

        name = QLabel(self.character.name or "（nameless）")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setProperty("class", "titlePrimary")
        outer.addWidget(name)

        if self.character.alias:
            alias = QLabel(self.character.alias)
            alias.setAlignment(Qt.AlignmentFlag.AlignCenter)
            alias.setProperty("class", "titleSecondary")
            outer.addWidget(alias)

        # ------------------------------------------------
        # Basic Info
        # ------------------------------------------------

        info = self._build_basic_info()
        outer.addWidget(info)

        outer.addStretch()

        # ------------------------------------------------
        # Footer (Petal Actions)
        # ------------------------------------------------

        # soft separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(220,180,210,0.35); border:none;")
        outer.addWidget(sep)

        footer = QWidget()
        footer.setProperty("class", "cardFooter")

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 6, 0, 0)
        footer_layout.setSpacing(8)

        if self.character.x_file is not None:
            x_btn = QPushButton("🔒 X FILE")
            x_btn.setProperty("role", "secondary")
            x_btn.clicked.connect(self._open_xfile_reader)
            footer_layout.addWidget(x_btn)

        footer_layout.addStretch()

        edit_btn = QPushButton("Open Editor")
        edit_btn.setProperty("role", "primary")
        edit_btn.clicked.connect(self.open_editor)
        footer_layout.addWidget(edit_btn)

        outer.addWidget(footer)

        return card


    # --------------------------------------------------
    # Content Area (Tabs + Editor)
    # --------------------------------------------------

    def _build_content_area(self):
        area = QVBoxLayout()
        area.setSpacing(6)

        area.addLayout(self._build_content_selector())
        area.addWidget(self._build_content_viewer(), 1)

        self._switch_content(0)
        return area
    
    def _build_content_selector(self):
        bar = QHBoxLayout()
        bar.setSpacing(6)

        self._content_buttons = []

        sections = [
            ("🌸Summary", self.character.summary),
            ("🌸Appearance", self.character.appearance),
            ("🌸Personality", self.character.personality),
            ("🌸Ability", self.character.ability),
        ]
        self._content_sections = sections

        for i, (title, _) in enumerate(sections):
            btn = QPushButton(title)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self.READER_BTN_INACTIVE)
            btn.clicked.connect(lambda _, x=i: self._switch_content(x))
            bar.addWidget(btn)
            self._content_buttons.append(btn)

        bar.addStretch()
        return bar

    def _build_content_viewer(self):
        self.content_viewer = QTextEdit()
        self.content_viewer.setReadOnly(True)

        return self.content_viewer

    def _switch_content(self, index: int):
        _, content = self._content_sections[index]
        self.content_viewer.setMarkdown((content or "").strip())

        for i, btn in enumerate(self._content_buttons):
            if i == index:
                btn.setStyleSheet(self.READER_BTN_ACTIVE)
            else:
                btn.setStyleSheet(self.READER_BTN_INACTIVE)

    # --------------------------------------------------
    # meta area (left)
    # --------------------------------------------------
    def _build_basic_info(self):
        box = QGroupBox("Basic Info")
        box.setProperty("class", "section")

        box.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum
        )

        grid = QGridLayout(box)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)

        # 四列：
        # label / value | label / value
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 0)
        grid.setColumnStretch(3, 1)

        fields = [
            ("Age", self.character.age),
            ("Gender", self.character.gender),
            ("Height", self.character.height),
            ("BWH", self.character.bwh),
            ("Hair", self.character.hair_color),
            ("Eyes", self.character.eye_color),
            ("Charm", getattr(self.character, "charm", None)),
            ("Capability", getattr(self.character, "capability", None)),
        ]

        visible = [(k, v) for k, v in fields if v]

        for i, (label, value) in enumerate(visible):
            row = i // 2
            col = (i % 2) * 2

            lab = QLabel(label)
            lab.setProperty("class", "fieldLabel")

            val = QLabel(str(value))
            val.setProperty("class", "fieldValue")
            val.setWordWrap(True)

            grid.addWidget(lab, row, col)
            grid.addWidget(val, row, col + 1)

        return box



    # --------------------------------------------------
    # XFILE
    # --------------------------------------------------
    def _open_xfile_reader(self):
        dlg = XFileArchiveReader(
            x_file=self.character.x_file,
            base_dir=self.json_path,
            parent=self
        )
        dlg.exec()

    # --------------------------------------------------
    # Editor
    # --------------------------------------------------
    def open_editor(self):
        dlg = CharacterEditorDialog(self)
        dlg.load_character(self.character)

        if self.json_path:
            dlg.current_json_path = self.json_path

        main = self.parent()
        if main and hasattr(main, "on_character_saved"):
            dlg.character_saved.connect(main.on_character_saved)

        dlg.exec()
        self.accept()


class QGroupFrame(QFrame):
    def __init__(self, title):
        super().__init__()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        label = QLabel(title)
        outer.addWidget(label)

        self._inner_layout = QGridLayout()
        outer.addLayout(self._inner_layout)

    def content_layout(self) -> QGridLayout:
        return self._inner_layout

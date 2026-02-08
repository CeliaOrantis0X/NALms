# app/ui/main_window.py
# NALms — Novel Assets Library Management System
# Version 2.0

import os
import json

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLineEdit, QLabel, QComboBox,
    QFileDialog, QScrollArea, QGridLayout,
    QFrame
)
from PyQt6.QtCore import Qt, QSettings

# from app.config.main_style_01 import DARK_THEME
from app.ui.characterEditor.editor import CharacterEditorDialog
from app.domain.character import Character
from app.ui.profile_reader import CharacterReaderDialog
from app.ui.theme_manager import ThemeManager


def highlight(text: str, keyword: str) -> str:
    """
    将 text 中命中的 keyword 用 HTML span 高亮
    """
    if not keyword:
        return text

    lower_text = text.lower()
    lower_kw = keyword.lower()

    start = lower_text.find(lower_kw)
    if start == -1:
        return text

    end = start + len(keyword)
    return (
        text[:start]
        + f"<span style='color:#ffd866; font-weight:bold;'>"
        + text[start:end]
        + "</span>"
        + text[end:]
    )


class CharacterListItem(QWidget):
    def __init__(self, character, keyword: str = "", on_click=None):
        super().__init__()
        self.character = character
        self.keyword = keyword
        self.on_click = on_click

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 10, 10, 10)

        # =====================
        # Name (主标题)
        # =====================
        name_text = character.name or "（nameless）"
        name = QLabel(highlight(name_text, self.keyword))
        name.setTextFormat(Qt.TextFormat.RichText)
        # name.setStyleSheet("font-size:15px; font-weight:bold;")
        layout.addWidget(name)

        # =====================
        # Media (次标题)
        # =====================
        media_text = (getattr(character, "media", "") or "").strip()

        if media_text:
            media = QLabel(highlight(media_text, self.keyword))
            # media.setStyleSheet("color:#aaa; font-size:12px;")
        else:
            media = QLabel("— Unknown Work —")

        media.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(media)

        # =====================
        # Meta row: age / height
        # =====================
        meta_parts = []
        if getattr(character, "age", None):
            meta_parts.append(f"{character.age}")
        if getattr(character, "height", None):
            meta_parts.append(f"{character.height}")

        if meta_parts:
            meta = QLabel(" · ".join(meta_parts))
            # meta.setStyleSheet("color:#888; font-size:11px;")
            layout.addWidget(meta)

        # =====================
        # Tags
        # =====================
        if character.tags:
            tag_parts = []
            for tag in character.tags:
                tag_parts.append(highlight(tag, self.keyword))

            tags = QLabel(" · ".join(tag_parts))
            tags.setTextFormat(Qt.TextFormat.RichText)
            # tags.setStyleSheet("color:#999; font-size:12px;")
            layout.addWidget(tags)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_click(self.character)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        ThemeManager.load()
        ThemeManager.apply(ThemeManager.current)

        self.setWindowTitle("NALms 2.0")
        self.resize(540, 360)

        # ===== 设置存储 =====
        self.settings = QSettings("NALms", "NALms2")

        # ===== 内存数据 =====
        self.current_folder: str | None = None
        self.characters: list[Character] = []
        self.search_index: list[str] = []

        self._build_ui()
        # self.setStyleSheet(DARK_THEME)

        # ★ 启动时恢复上次目录
        self._restore_last_folder()

    # ======================================================
    # UI
    # ======================================================
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setSpacing(16)

        root.addLayout(self._build_left_panel(), stretch=3)
        root.addLayout(self._build_right_panel(), stretch=1)

    # ======================================================
    # 左侧
    # ======================================================
    def _build_left_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)

        folder_row = QHBoxLayout()
        self.folder_label = QLabel("Current Folder:")
        folder_btn = QPushButton("Select Folder")
        folder_btn.clicked.connect(self.choose_folder)

        folder_row.addWidget(self.folder_label)
        folder_row.addWidget(folder_btn)
        layout.addLayout(folder_row)

        # ===== 搜索行（浏览器风格）=====
        search_row = QHBoxLayout()
        search_row.setSpacing(6)

        search_btn = QPushButton("🔍")
        search_btn.setFixedSize(48, 32)

        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.clicked.connect(self.apply_search)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search name / tag / media/ summary ")
        self.search_input.textChanged.connect(self.apply_search)
        self.search_input.returnPressed.connect(self.apply_search)
        self.search_input.textChanged.connect(self.apply_search)

        search_row.addWidget(search_btn)
        search_row.addWidget(self.search_input, 1)

        layout.addLayout(search_row)

        # ===== 角色卡片列表 =====
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid.setSpacing(12)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, stretch=1)

        bottom_row = QHBoxLayout()
        clear_btn = QPushButton("Clear Results")
        clear_btn.clicked.connect(self.clear_results)

        bottom_row.addStretch()
        bottom_row.addWidget(clear_btn)
        layout.addLayout(bottom_row)

        return layout

    # ======================================================
    # 右侧
    # ======================================================
    def _build_right_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        editor_btn = QPushButton("Character Editor")
        editor_btn.setFixedHeight(44)
        editor_btn.clicked.connect(self.open_character_editor)
        layout.addWidget(editor_btn)

        # =========================
        # Theme selector
        # =========================
        theme_box = QComboBox()
        theme_box.addItems(ThemeManager.available())
        theme_box.setCurrentText(ThemeManager.current)
        theme_box.currentTextChanged.connect(ThemeManager.apply)

        layout.addWidget(QLabel("Theme"))
        layout.addWidget(theme_box)

        layout.addStretch()
        return layout

    # ======================================================
    # 行为
    # ======================================================
    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.current_folder = folder
        self.folder_label.setText(folder)

        # ★ 存储上次目录
        self.settings.setValue("last_folder", folder)

        self.load_characters_from_folder(folder)
        self.refresh_cards(self.characters)

    def load_characters_from_folder(self, folder: str):
        self.characters.clear()
        self.search_index.clear()

        for filename in os.listdir(folder):
            # ★ 明确排除草稿 / 隐藏 / 临时文件
            if not filename.endswith(".json"):
                continue
            if filename.startswith("_") or filename.startswith("."):
                continue

            path = os.path.join(folder, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            if not isinstance(data, dict):
                continue

            c = Character.from_dict(data)
            c._source_path = path

            self.characters.append(c)
            self.search_index.append(c.searchable_text())
            

    def apply_search(self):
        if not self.characters:
            return

        keyword = self.search_input.text().strip().lower()
        if not keyword:
            self.refresh_cards(self.characters)
            return

        result = [
            c for c, blob in zip(self.characters, self.search_index)
            if keyword in blob
        ]
        self.refresh_cards(result)

    def clear_results(self):
        self.search_input.clear()
        self.refresh_cards(self.characters)

    # 恢复上次目录
    def _restore_last_folder(self):
        folder = self.settings.value("last_folder", type=str)
        if not folder:
            return
        if not os.path.isdir(folder):
            return

        self.current_folder = folder
        self.folder_label.setText(folder)

        self.load_characters_from_folder(folder)
        self.refresh_cards(self.characters)

    # ===============================
    # UI 工具
    # ===============================
    def refresh_cards(self, characters: list[Character]):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for i, char in enumerate(characters):
            item = CharacterListItem(
                char,
                keyword=self.search_input.text().strip(),
                on_click=self.open_character_reader
            )
            self.grid.addWidget(item, i, 0)

    def open_character_reader(self, character):
        dlg = CharacterReaderDialog(
            character,
            json_path=getattr(character, "_source_path", None),
            parent=self
        )
        dlg.exec()

        if getattr(dlg, "editor_saved_path", None):
            self.reload_character(dlg.editor_saved_path)

    def reload_character(self, json_path: str):
        if not self.current_folder:
            return

        self.load_characters_from_folder(self.current_folder)
        self.apply_search()


    def _build_simple_card(self, char: Character) -> QWidget:
        """
        不依赖 CharacterCard 的最简角色展示单元
        """
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        name = QLabel(char.name or "Unnamed")
        # name.setStyleSheet("font-weight: bold; font-size: 14px;")

        alias = QLabel(char.alias)
        
        # alias.setStyleSheet("color: #aaa; font-size: 11px;")

        tags = QLabel(", ".join(char.tags) if char.tags else "")
        # tags.setStyleSheet("color: #888; font-size: 11px;")

        intro = QLabel((char.intro or "")[:80])
        intro.setWordWrap(True)
        # intro.setStyleSheet("color: #bbb; font-size: 11px;")

        layout.addWidget(name)
        if char.alias:
            layout.addWidget(alias)
        if char.tags:
            layout.addWidget(tags)
        if char.intro:
            layout.addWidget(intro)

        return frame

    # ======================================================
    # Editor
    # ======================================================
    def open_character_editor(self):
        dlg = CharacterEditorDialog(self)
        dlg.character_saved.connect(self.on_character_saved)
        dlg.exec()

    def on_character_saved(self, file_path: str):
        if not self.current_folder:
            return
        if not file_path.startswith(self.current_folder):
            return

        self.load_characters_from_folder(self.current_folder)
        self.apply_search()

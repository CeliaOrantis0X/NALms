# app/ui/main_window.py
# NALms — Novel Assets Library Management System
# Version 2.0

import os
import json

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLineEdit, QLabel, QComboBox,
    QFileDialog, QScrollArea, QGridLayout,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush

from app.ui.characterEditor.editor import CharacterEditorDialog
from app.domain.character import Character
from app.ui.characterEditor.profile_reader import CharacterReaderDialog
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
    MIN_AVATAR_SIZE = 100  # 最小图像直径，避免卡片内容太少时太小

    def __init__(self, character, keyword: str = "", on_click=None):
        super().__init__()
        self.setProperty("class", "card")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.character = character
        self.keyword = keyword
        self.on_click = on_click
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # ===== 外层水平布局 =====
        outer_layout = QHBoxLayout(self)
        outer_layout.setSpacing(10)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        # =====================
        # Avatar 区域
        # =====================
        self.avatar_label = QLabel()
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setProperty("class", "cardAvatar")
        self.avatar_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        outer_layout.addWidget(self.avatar_label)

        # =====================
        # 右侧信息列
        # =====================
        self.info_widget = QWidget()
        self.info_widget.setProperty("class", "cardInfo")
        self.info_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        self.info_layout = QVBoxLayout(self.info_widget)
        self.info_layout.setSpacing(2)
        self.info_layout.setContentsMargins(0, 0, 0, 0)

        outer_layout.addWidget(
            self.info_widget,
            alignment=Qt.AlignmentFlag.AlignTop
        )

        # ID在Name同行右侧显示，和Name呈两端对齐，举例ID: S10001
        # =====================================
        # Name + ID Row
        # =====================================

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        # ---- Name ----

        name_text = character.name or "（nameless）"

        name = QLabel(highlight(name_text, self.keyword))
        name.setTextFormat(Qt.TextFormat.RichText)
        name.setProperty("class", "cardName")
        name.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        title_row.addWidget(name)

        # ---- Push Stretch ----

        title_row.addStretch()

        # ---- ID ----

        char_id = getattr(character, "id", "") or ""

        id_label = QLabel(f"ID: {char_id}")
        id_label.setProperty("class", "cardId")

        title_row.addWidget(id_label)

        # ---- Add Row ----

        self.info_layout.addLayout(title_row)
        

        # 次级信息容器（统一缩进）
        sub_layout = QVBoxLayout()
        sub_layout.setSpacing(2)
        sub_layout.setContentsMargins(16, 0, 0, 0)  # 左缩进
        self.info_layout.addLayout(sub_layout)

        # Media
        media_text = (getattr(character, "media", "") or "").strip()
        media_label = (
            QLabel(highlight(media_text, self.keyword))
            if media_text else QLabel("— Unknown Work —")
        )
        media_label.setTextFormat(Qt.TextFormat.RichText)
        sub_layout.addWidget(media_label)

        # Meta
        meta_parts = []
        if getattr(character, "age", None):
            meta_parts.append(f"{character.age}")
        if getattr(character, "height", None):
            meta_parts.append(f"{character.height}")
        if meta_parts:
            meta = QLabel(" ｜ ".join(meta_parts))
            sub_layout.addWidget(meta)

        # Tags
        if character.tags:
            tag_parts = [highlight(tag, self.keyword) for tag in character.tags]
            tags = QLabel(" · ".join(tag_parts))
            tags.setTextFormat(Qt.TextFormat.RichText)
            sub_layout.addWidget(tags)

        # ===== 设置头像 =====
        self._set_avatar(character)

    def _set_avatar(self, character):
        size = self.MIN_AVATAR_SIZE
        avatar_path = getattr(character, "image", None)

        if avatar_path and os.path.isfile(avatar_path):
            pix = QPixmap(avatar_path)
            if not pix.isNull():
                # 以宽度为基准缩放，保证上部在上方
                scale = size / pix.width()
                new_w = size
                new_h = int(pix.height() * scale)

                pix = pix.scaled(
                    new_w,
                    new_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                # 从顶部裁切
                if pix.height() > size:
                    pix = pix.copy(0, 0, size, size)
            else:
                pix = self._placeholder_pixmap(size)
        else:
            pix = self._placeholder_pixmap(size)

        self.avatar_label.setPixmap(pix)


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.on_click:
            self.on_click(self.character)

    def _placeholder_pixmap(self, size: int):
        placeholder = QPixmap(size, size)
        placeholder.fill(Qt.GlobalColor.transparent)
        painter = QPainter(placeholder)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(200, 160, 220, 100)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size, size)
        painter.end()
        return placeholder


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        ThemeManager.load()
        ThemeManager.apply(ThemeManager.current)

        self.setWindowTitle("NALms")
        self.resize(720, 480)

        # ===== 设置存储 =====
        self.settings = QSettings("NALms")

        # ===== 内存数据 =====
        self.current_folder: str | None = None
        self.characters: list[Character] = []
        self.search_index: list[str] = []

        self._build_ui()

        # ★ 启动时恢复上次目录
        self._restore_last_folder()

    # ======================================================
    # UI
    # ======================================================
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(12,12,12,12)

        root.addLayout(self._build_left_panel(), stretch=3)
        root.addSpacing(12)
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
        folder_btn.setProperty("role", "primary")
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

        self.grid.setColumnStretch(0, 1)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, stretch=1)

        bottom_row = QHBoxLayout()
        clear_btn = QPushButton("Clear Results")
        clear_btn.setProperty("role", "secondary")
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

        editor_btn = QPushButton("Open Editor")
        editor_btn.setFixedHeight(44)
        editor_btn.setProperty("role", "primary")
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

        for root, dirs, files in os.walk(folder):
            # 可选：跳过隐藏文件夹 / 特殊目录
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".") and not d.startswith("_")
            ]

            for filename in files:
                if not filename.endswith(".json"):
                    continue
                if filename.startswith("_") or filename.startswith("."):
                    continue

                path = os.path.join(root, filename)

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

        matched = []

        for c, blob in zip(self.characters, self.search_index):
            if keyword not in blob:
                continue

            name = (c.name or "").lower()

            # 优先级：name 命中最前
            priority = 0 if keyword in name else 1

            matched.append((priority, c))

        # 按优先级排序（稳定）
        matched.sort(key=lambda x: x[0])

        result = [c for _, c in matched]

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

        self.grid.setRowStretch(len(characters), 1)

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

        alias = QLabel(char.alias)
        
        tags = QLabel(", ".join(char.tags) if char.tags else "")

        summary = QLabel((char.summary or "")[:80])
        summary.setWordWrap(True)

        layout.addWidget(name)
        if char.alias:
            layout.addWidget(alias)
        if char.tags:
            layout.addWidget(tags)
        if char.summary:
            layout.addWidget(summary)

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

# app/ui/characterEditor/editor.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QStackedWidget,
    QPushButton, QFileDialog, QWidget, QFrame,
    QTextEdit, QGroupBox, QMessageBox
)

from PyQt6.QtGui import QPixmap, QImageReader
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from pathlib import Path
import copy
import logging

from app.ui.characterEditor.editor_status import EditorStatus
from app.domain.character import Character
from app.ui.panels.xfile_editor import XFileDialog
from app.ui.characterEditor.editor_session import EditorSession
from app.infrastructure.repository import Repository
from app.application.character_mapper import CharacterMapper
from app.ui.characterEditor.field_schema import BIO_FIELDS
from app.utils.story_parser import parse_story_file
from app.utils.text_reader import read_text_safely
from app.utils.paths import absolutize

from app.ui.panels.profile_panel import build_profile_card
from app.ui.panels.bio_panel import build_bio_panel
from app.ui.panels.misc_panel import build_misc_panel

from app.ui.content.content_editor import create_content_editors
from app.ui.panels.image_utils import (
    select_image_file,
    load_image_to_label
)


# ==================================================
# editor dialog
# ==================================================

class CharacterEditorDialog(QDialog):

    character_saved = pyqtSignal(str)
    # ↑ 传出保存后的 json 文件路径

    # ==================================================
    # lifecycle
    # ==================================================

    def __init__(self, parent=None):
        super().__init__(parent)

        self._loading = False

        self.model: Character | None = None
        self.xfile_model: dict | None = None

        self.session = EditorSession()

        self.widgets = {}

        self.current_path = None
        self.model_image_path = None
        self.story_blocks = []

        self.setWindowTitle("Character Editor")
        self.resize(720, 800)

        self._build_ui()
        self._bind_fields()
        self._setup_autosave()

    # ==================================================
    # UI root
    # ==================================================

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)

        root.addLayout(self._build_toolbar())
        root.addLayout(self._build_editor_area())
        root.addWidget(self._build_story_panel())

    # ==================================================
    # toolbar
    # ==================================================

    def _build_toolbar(self):
        bar = QHBoxLayout()
        bar.setSpacing(12)

        import_btn = QPushButton("IMPORT")
        import_btn.setProperty("role", "secondary")
        import_btn.clicked.connect(self.import_json)

        self.save_btn = QPushButton("SAVE")
        self.save_btn.setProperty("role", "primary")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_json)

        xfile_btn = QPushButton("X FILE")
        xfile_btn.setProperty("role", "secondary")
        xfile_btn.clicked.connect(self.open_xfile)

        ok_btn = QPushButton("CONFIRM")
        ok_btn.setProperty("role", "primary")
        ok_btn.clicked.connect(self.on_confirm)

        self.reset_btn = QPushButton("RESET")
        self.reset_btn.setProperty("role", "ghost")
        self.reset_btn.clicked.connect(self.reset_editor)

        self.status = EditorStatus(self)
        self.status.setFixedHeight(24)

        bar.addWidget(xfile_btn)
        bar.addWidget(import_btn)
        bar.addWidget(self.save_btn)
        bar.addStretch()
        bar.addWidget(self.status)
        bar.addStretch()
        bar.addWidget(ok_btn)
        bar.addWidget(self.reset_btn)

        return bar

    # ==================================================
    # editor area (meta + content)
    # ==================================================

    def _build_editor_area(self):
        area = QVBoxLayout()
        area.setSpacing(12)

        area.addLayout(self._build_meta_area(), 1)

        # =================
        # Divider
        # =================
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setProperty("class", "softDivider")

        area.addWidget(divider)

        area.addLayout(self._build_content_area(), 1)
        return area

    # --------------------------
    # meta area (upper)
    # --------------------------
    def _build_meta_area(self):
        layout = QHBoxLayout()
        layout.setSpacing(16)

        layout.addLayout(self._build_meta_left_panel(), 1)
        layout.addLayout(self._build_meta_right_panel(), 2)

        return layout

    def _build_meta_left_panel(self):
        box = QVBoxLayout()
        box.setSpacing(8)

        # box.addWidget(self._build_avatar_panel())
        # box.addWidget(self._build_rating_panel())
        box.addWidget(self._build_profile_card())
        box.addStretch()

        return box

    def _build_meta_right_panel(self):
        box = QVBoxLayout()
        box.setSpacing(8)

        box.addWidget(self._build_bio_panel(), 2)
        box.addWidget(self._build_misc_panel(), 1)

        return box

    # --------------------------
    # meta panels
    # --------------------------

    def _build_profile_card(self):
        return build_profile_card(self)

    # 基本信息
    def _build_bio_panel(self):
        return build_bio_panel(self)

    def _build_misc_panel(self):
        return build_misc_panel(self)

    # --------------------------
    # content area (lower)
    # --------------------------

    def _build_content_area(self):
        box = QVBoxLayout()
        box.setSpacing(6)

        selector = self._build_content_selector()
        editor = self._build_content_editor()

        box.addLayout(selector)
        box.addWidget(editor)

        self._switch_text_block(0)
        return box

    def _build_content_selector(self):

        bar = QHBoxLayout()
        bar.setSpacing(6)

        self.text_stack = QStackedWidget()
        self._text_buttons = []

        configs = create_content_editors(self)

        for i, (key, title) in enumerate(configs):

            editor = self.text_editors[key]

            self.text_stack.addWidget(editor)

            btn = QPushButton(title)

            btn.setCheckable(True)
            btn.setObjectName("contentTab")

            btn.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            btn.clicked.connect(
                lambda _, x=i: self._switch_text_block(x)
            )

            self._text_buttons.append(btn)

            bar.addWidget(btn)

        self._text_buttons[0].setChecked(True)

        self.text_stats_label = QLabel("")

        bar.addStretch()
        bar.addWidget(self.text_stats_label)

        return bar

    def _build_content_editor(self):
        return self.text_stack

    def _switch_text_block(self, index: int):
        self.text_stack.setCurrentIndex(index)

        # tab按钮状态
        for i, btn in enumerate(self._text_buttons):
            btn.setChecked(i == index)

        # editor active状态
        for i in range(self.text_stack.count()):

            editor = self.text_stack.widget(i)

            is_active = (i == index)

            editor.setProperty("active", is_active)

            # 强制刷新QSS
            editor.style().unpolish(editor)
            editor.style().polish(editor)

        self._update_text_stats()

    # 文本统计函数
    def _update_text_stats(self):
        editor = self.text_stack.currentWidget()
        if not isinstance(editor, QTextEdit):
            self.text_stats_label.setText("")
            return

        text = editor.toPlainText()
        if not text.strip():
            self.text_stats_label.setText("0 字 / 0 行")
            return

        char_count = len(text.replace("\n", ""))
        line_count = text.count("\n") + 1

        self.text_stats_label.setText(f"{char_count} 字 / {line_count} 行")

    # ==================================================
    # story
    # ==================================================
    def _build_story_panel(self):
        if hasattr(self, "story_group"):
            return self.story_group

        self.story_group = QGroupBox("Story")
        l = QHBoxLayout(self.story_group)

        btn = QPushButton("Import File")
        btn.setProperty("role", "secondary")
        btn.clicked.connect(self.import_story)

        self.story_label = QLabel(" No story imported ")
        self.story_label.setProperty("class", "storyHint")

        l.addWidget(btn)
        l.addWidget(self.story_label)
        l.addStretch()

        return self.story_group

    # ==================================================
    # remaining logic unchanged
    # ==================================================

    # --------------------------------------------------
    # field binding
    # --------------------------------------------------

    def _bind_fields(self):

        self.bindings = {}

        for field in BIO_FIELDS:
            self.bindings[field["key"]] = self.widgets[field["key"]]

        self.bindings.update({
            "charm": self.charm_cb,
            "capability": self.capability_cb,
            "media": self.media_input,
            "partnership": self.partnership_input,
        })

        for editor in self.text_editors.values():
            editor.textChanged.connect(
                self._update_text_stats
            )

        for w in self.bindings.values():
            if isinstance(w, QComboBox):
                w.currentTextChanged.connect(self._update_dirty_state)
            else:
                w.textChanged.connect(self._update_dirty_state)

        self.tag_input.textChanged.connect(self._update_dirty_state)

        for editor in self.text_editors.values():
            editor.textChanged.connect(
                self._update_dirty_state
            )

    # --------------------------------------------------
    # data <-> ui
    # --------------------------------------------------

    def _base_dir(self):
        """当前角色 JSON 所在目录；新建 / 尚未保存时为 None。"""
        return Path(self.current_path).parent if self.current_path else None

    def _clear_avatar(self):
        self.avatar.clear()
        self.avatar.setText("No Image\nClick Import")

    def load_model(self, model: Character):
        # 深拷贝：编辑器里的任何改动都不能影响调用方
        # （主窗口的角色列表、阅读器）持有的同一个对象。
        model = copy.deepcopy(model)

        # 编辑器内部统一使用绝对路径；写盘时由 Repository.prepare_for_save 转回相对路径
        base_dir = self._base_dir()
        model.image = absolutize(model.image, base_dir)
        if isinstance(model.x_file, dict):
            model.x_file["image"] = absolutize(model.x_file.get("image"), base_dir)

        self._loading = True

        try:

            CharacterMapper.load(self, model)

            self.xfile_model = (
                model.x_file
                if isinstance(model.x_file, dict)
                else None
            )

            self.model_image_path = model.image

            # 没有图片 / 图片读取失败时也要清掉旧头像，
            # 否则 RESET 或切换到无头像角色后仍显示上一个人的图
            if not (
                model.image
                and load_image_to_label(self.avatar, model.image)
            ):
                self._clear_avatar()

        finally:
            self._loading = False

        self.session.load_character(model,self.current_path)

        self._update_dirty_state()


    def collect_model(self) -> Character:
        return CharacterMapper.collect(self)

    # Auto-save
    def _setup_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(30_000)  # 30 秒
        self.autosave_timer.timeout.connect(self._autosave_draft)
        self.autosave_timer.start()

    # 自动保存草稿
    def _autosave_draft(self):
        # 定时器回调里的异常会落到全局异常钩子并弹窗；
        # 自动保存是后台行为，失败只记日志，不打扰用户。
        try:
            model = self.collect_model()
            self.session.autosave(model)
        except Exception:
            logging.exception("autosave failed")

    # 清除自动保存草稿
    def _clear_autosave_draft(self):
        draft_path = Path("app/drafts/character_editor_autosave.json")
        if draft_path.exists():
            draft_path.unlink()

    def _update_dirty_state(self):

        if self._loading:
            return

        model = self.collect_model()

        self.session.update_snapshot(model)

        self.save_btn.setEnabled(self.session.is_dirty())


    # 关闭窗口时 Dirty 提示
    def closeEvent(self, event):
        if not self.session.is_dirty():
            event.accept()
            return

        box = QMessageBox(self)
        box.setWindowTitle("Unsaved Changes")
        box.setText("There are unsaved changes.")
        box.setIcon(QMessageBox.Icon.Warning)

        save_btn = box.addButton("Save", QMessageBox.ButtonRole.AcceptRole)
        discard_btn = box.addButton("Discard", QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

        box.exec()

        clicked = box.clickedButton()

        if clicked == save_btn:
            # 用户在“另存为”里点了取消、或写盘失败时，必须留在编辑器里
            if self.save_json():
                event.accept()
            else:
                event.ignore()
        elif clicked == discard_btn:
            event.accept()
        else:
            event.ignore()

    # --------------------------------------------------
    # io
    # --------------------------------------------------

    def import_json(self):
        file, _ = QFileDialog.getOpenFileName(self, "Import", "", "JSON (*.json)")
        if not file:
            return

        try:
            c = Repository.load_from_json(file)
        except Exception as e:
            logging.exception("import failed: %s", file)
            QMessageBox.warning(
                self,
                "Import Failed",
                f"Could not read this file:\n{file}\n\n{e}"
            )
            self.status.error(f"Import failed：{Path(file).name}")
            return

        # 先设置 current_path：load_model 要用它解析相对素材路径
        self.current_path = file

        self.load_model(c)

        self.status.success(f"Import successful：{Path(file).name}")

    def _write_model(self, model: Character, file: str) -> bool:
        """
        写盘。成功返回 True；失败（弹窗提示）返回 False。
        写的是 model 的副本：prepare_for_save 会把素材路径改成相对路径，
        不能让它反过来改到界面上的状态。
        """
        to_write = copy.deepcopy(model)

        try:
            Repository.prepare_for_save(to_write, file)
            Repository.save_to_json(file, to_write)
        except Exception as e:
            logging.exception("save failed: %s", file)
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Could not save:\n{file}\n\n{e}"
            )
            self.status.error(f"Save failed：{Path(file).name}")
            return False

        self.current_path = file

        # 基线用 model（绝对路径，与界面状态一致），而不是 to_write（已转相对路径）
        self.session.reset_dirty(model)
        self.session.clear_autosave()
        self.save_btn.setEnabled(self.session.is_dirty())

        self.character_saved.emit(file)

        self.status.success(f"Save → {file}")
        return True

    def save_json(self) -> bool:
        model = self.collect_model()

        file, _ = QFileDialog.getSaveFileName(self, "Save", "", "JSON (*.json)")
        if not file:
            return False

        return self._write_model(model, file)

    def on_confirm(self) -> bool:
        if not self.current_path:
            QMessageBox.information(
                self,
                "No File",
                "Please import or create a new file first"
            )
            self.status.warning("CONFIRM failed：no file selected")
            return False

        return self._write_model(self.collect_model(), self.current_path)

    # --------------------------------------------------
    # reset editor
    # --------------------------------------------------

    def reset_editor(self):
        reply = QMessageBox.question(
            self,
            "Reset Editor",
            "Reset editor Yes/No\n",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # —— 清空编辑器 Session 状态 ——
        self.current_path = None
        self.model_image_path = None
        self.story_blocks = []

        # —— 清空 UI（包含所有外部导入内容）——
        # load_model 内部会重建脏检测基线、回到干净状态。
        # 不要再单独调用 session.reset_dirty()：它需要 model 参数，无参调用会 TypeError。
        self.load_model(Character())
        self.save_btn.setEnabled(False)

        self.status.warning("Editor has been reset")

    # --------------------------------------------------
    # image and story import
    # --------------------------------------------------

    def _import_image(self):
        '''
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if not file:
            return

        reader = QImageReader(file)
        image = reader.read()

        if image.isNull():
            QMessageBox.warning(self, "Image Error", "Failed to load image")
            return

        pixmap = QPixmap.fromImage(image)
        self.model_image_path = file
        self.avatar.setPixmap(
            pixmap.scaled(
                self.avatar.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

        self._update_dirty_state()
        '''

        file = select_image_file(self)

        if not file:
            return

        ok = load_image_to_label(
            self.avatar,
            file
        )

        if not ok:
            QMessageBox.warning(
                self,
                "Image Error",
                "Failed to load image"
            )
            return

        self.model_image_path = file

        self._update_dirty_state()

    def import_story(self):
        file, _ = QFileDialog.getOpenFileName(self, "Story", "", "Text (*.txt *.md)")
        if not file:
            return

        # parse_story_file 返回 list[dict]，可直接 JSON 序列化
        self.story_blocks = parse_story_file(read_text_safely(file))
        self.story_label.setText(f"{len(self.story_blocks)} stories imported")

        self._update_dirty_state()

    # --------------------------------------------------
    # 内部方法
    # --------------------------------------------------

    # xfile入口
    def open_xfile(self):
        dlg = XFileDialog(
            model=self.xfile_model,
            parent=self,
            base_dir=self._base_dir()
        )

        if dlg.exec():
            self.xfile_model = dlg.get_model()
            self._update_dirty_state()

    # --------------------------------------------------
    # 外部方法
    # --------------------------------------------------

    def _create_widget_from_schema(self, field: dict):

        widget_cls = field["widget"]

        widget = widget_cls()

        if isinstance(widget, QComboBox):
            widget.addItems(field.get("items", []))

        widget.setProperty("class", "fieldInput")

        self.widgets[field["key"]] = widget

        return widget

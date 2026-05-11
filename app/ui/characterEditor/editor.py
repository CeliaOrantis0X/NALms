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
import json

from app.ui.characterEditor.editor_status import EditorStatus
from app.domain.character import Character
from app.ui.panels.xfile_editor import XFileDialog
from app.ui.characterEditor.editor_session import EditorSession

# ==================================================
# helpers
# ==================================================

def parse_story_file(text: str):
    blocks = text.split("\n---\n")
    stories = []
    for i, block in enumerate(blocks, 1):
        lines = block.strip().splitlines()
        title = lines[0].lstrip("# ").strip() if lines else f"Story {i}"
        content = "\n".join(lines[1:]).strip()
        stories.append({"title": title, "content": content})
    return stories

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

        self.model: Character | None = None
        self.xfile_model: dict | None = None

        self.session = EditorSession()

        # self.image_path = None
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
        card = QWidget()
        card.setProperty("class", "card")
        card.setFixedWidth(300)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # =================
        # Avatar
        # =================

        self.avatar = QLabel("No Image\nClick Import")
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setObjectName("Avatar")
        self.avatar.setFixedHeight(300)

        import_btn = QPushButton("Import Image")
        import_btn.clicked.connect(self._import_image)
        import_btn.setFixedHeight(28)

        layout.addWidget(self.avatar)
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

        self.charm_cb = QComboBox()
        self.charm_cb.addItems(["", "SSS+", "SSS", "SS", "S", "A"])

        self.capability_cb = QComboBox()
        self.capability_cb.addItems(["", "Lv6", "Lv5", "Lv4", "Lv3", "Lv2", "Lv1", "Lv0"])

        for w in (self.charm_cb, self.capability_cb):
            w.setProperty("class", "fieldInput")

        fields = [
            ("Charm", self.charm_cb),
            ("Capability", self.capability_cb),
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

    # 基本信息
    def _build_bio_panel(self):
        g = QGroupBox("Biography")
        l = QGridLayout(g)

        self.id_input = QLineEdit()
        self.name_input = QLineEdit()
        self.alias_input = QLineEdit()

        self.gender_cb = QComboBox()
        self.gender_cb.addItems(["", "女", "男"])

        self.age_input = QLineEdit()
        self.birthdate_input = QLineEdit()
        self.constellation_input = QLineEdit()
        self.hair_color_input = QLineEdit()
        self.eye_color_input = QLineEdit()
        self.height_input = QLineEdit()
        self.weight_input = QLineEdit()
        self.bwh_input = QLineEdit()

        self.weapon_input = QLineEdit()
        self.identity_input = QLineEdit()
        self.rank_input = QLineEdit()

        # 所有输入统一 class
        for w in (
            self.id_input,
            self.name_input,
            self.alias_input,
            self.gender_cb,
            self.age_input,
            self.birthdate_input,
            self.hair_color_input,
            self.eye_color_input,
            self.height_input,
            self.weight_input,
            self.bwh_input,
            self.weapon_input,
            self.identity_input,
            self.rank_input,
        ):
            w.setProperty("class", "fieldInput")

        fields = [
            ("ID", self.id_input),
            ("Name", self.name_input),
            ("Alias", self.alias_input),
            ("Gender", self.gender_cb),
            ("Age", self.age_input),
            ("Birthdate", self.birthdate_input),
            ("Hair", self.hair_color_input),
            ("Eyes", self.eye_color_input),
            ("Height", self.height_input),
            ("Weight", self.weight_input),
            ("BWH", self.bwh_input),
            ("Weapon", self.weapon_input),
            ("Identity", self.identity_input),
            ("Rank", self.rank_input),
        ]

        for i, (label, widget) in enumerate(fields):
            r = i // 2
            c = (i % 2) * 2

            lab = QLabel(label)
            lab.setProperty("class", "fieldLabel")

            l.addWidget(lab, r, c)
            l.addWidget(widget, r, c + 1)

        return g


    def _build_misc_panel(self):
        g = QGroupBox("Misc")
        l = QGridLayout(g)

        self.tag_input = QLineEdit()
        # self.personality_input = QLineEdit()
        self.partnership_input = QLineEdit()
        self.media_input = QLineEdit()

        # 给输入框统一打 class
        for w in (self.tag_input, self.partnership_input, self.media_input):
            w.setProperty("class", "fieldInput")

        fields = [
            ("Media", self.media_input),
            ("Partnership", self.partnership_input),
            ("Tags", self.tag_input),
            # ("Personality", self.personality_input),
        ]

        for i, (label, widget) in enumerate(fields):
            lab = QLabel(label)
            lab.setProperty("class", "fieldLabel")   # ← 关键

            row = i // 2
            col = (i % 2) * 2

            l.addWidget(lab, row, col)
            l.addWidget(widget, row, col + 1)

        return g
    
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

        self.edit_appearance = QTextEdit()
        self.edit_summary = QTextEdit()
        self.edit_personality = QTextEdit()
        self.edit_ability = QTextEdit()

        for editor in (
            self.edit_appearance,
            self.edit_summary,
            self.edit_personality,
            self.edit_ability
        ):
            editor.setObjectName("contentEditor")

        editors = [
            ("Appearance", self.edit_appearance),
            ("Summary", self.edit_summary),
            ("Personality", self.edit_personality),
            ("Ability", self.edit_ability),
        ]

        for i, (name, editor) in enumerate(editors):
            self.text_stack.addWidget(editor)

            btn = QPushButton(name)
            btn.setCheckable(True)                 
            btn.setObjectName("contentTab")         #  限定qss范围
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            btn.clicked.connect(lambda _, x=i: self._switch_text_block(x))

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
        self.bindings = {
            "id": self.id_input,
            "name": self.name_input,
            "alias": self.alias_input,
            "gender": self.gender_cb,
            "age": self.age_input,
            "birthdate": self.birthdate_input,
            "constellation": self.constellation_input,
            "hair_color": self.hair_color_input,
            "eye_color": self.eye_color_input,
            "height": self.height_input,
            "weight": self.weight_input,
            "bwh": self.bwh_input,

            "charm": self.charm_cb,
            "capability": self.capability_cb,

            "weapon": self.weapon_input,
            # "ability": self.ability_input,
            "identity": self.identity_input,
            "rank": self.rank_input,
            # "capability": self.capability_input,
            
            # "personality": self.personality_input,
            "media": self.media_input,
            "partnership": self.partnership_input,
        }

        for editor in [
            self.edit_summary,
            self.edit_appearance,
            self.edit_personality,
            self.edit_ability
        ]:
            editor.textChanged.connect(self._update_text_stats)

        for w in self.bindings.values():
            if isinstance(w, QComboBox):
                w.currentTextChanged.connect(self._update_dirty_state)
            else:
                w.textChanged.connect(self._update_dirty_state)

        self.tag_input.textChanged.connect(self._update_dirty_state)

        self.edit_summary.textChanged.connect(self._update_dirty_state)
        self.edit_appearance.textChanged.connect(self._update_dirty_state)
        self.edit_personality.textChanged.connect(self._update_dirty_state)
        self.edit_ability.textChanged.connect(self._update_dirty_state)       

    # --------------------------------------------------
    # data <-> ui
    # --------------------------------------------------

    def load_model(self, model: Character):
        self.model = model
        self.xfile_model = model.x_file if isinstance(model.x_file, dict) else None
        self.session.load_character(model, self.current_path)

        for k, w in self.bindings.items():
            v = getattr(model, k, "")
            if isinstance(w, QComboBox):
                w.setCurrentText(v)
            else:
                w.setText(v)

        self.tag_input.setText(", ".join(model.tags))

        self.edit_summary.setPlainText(model.summary)
        self.edit_appearance.setPlainText(model.appearance)
        self.edit_personality.setPlainText(model.personality)
        self.edit_ability.setPlainText(model.ability)

        self.story_blocks = model.stories or []
        self.story_label.setText(
            f"{len(self.story_blocks)} stories imported"
            if self.story_blocks else " "
        )

        self.model_image_path = model.image
        if model.image and Path(model.image).exists():
            pix = QPixmap(model.image)
            if not pix.isNull():
                self.avatar.setPixmap(
                    pix.scaled(
                        self.avatar.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )
        else:
            self.avatar.clear()

        self._update_dirty_state()


    def collect_model(self) -> Character:
        model = Character()

        for k, w in self.bindings.items():
            value = w.currentText() if isinstance(w, QComboBox) else w.text()
            setattr(model, k, value)

        model.tags = [t.strip() for t in self.tag_input.text().split(",") if t.strip()]

        model.summary = self.edit_summary.toPlainText()
        model.appearance = self.edit_appearance.toPlainText()
        model.personality = self.edit_personality.toPlainText()
        model.ability = self.edit_ability.toPlainText()

        model.stories = self.story_blocks
        model.image = self.model_image_path

        if isinstance(self.xfile_model, dict):
            model.x_file = self.xfile_model
        else:
            model.x_file = None

        return model
    
    # Auto-save
    def _setup_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(30_000)  # 30 秒
        self.autosave_timer.timeout.connect(self._autosave_draft)
        self.autosave_timer.start()

    # 自动保存草稿
    def _autosave_draft(self):
        self.session.character = self.collect_model()
        self.session.autosave()   

    # 清除自动保存草稿
    def _clear_autosave_draft(self):
        draft_path = Path("app/drafts/character_editor_autosave.json")
        if draft_path.exists():
            draft_path.unlink()

    def _update_dirty_state(self):
        model = self.collect_model()
        snapshot = self.session._make_snapshot()
        self.session.mark_dirty_if_needed(snapshot)
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
            self.save_json()
            event.accept()
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

        data = json.load(open(file, encoding="utf-8"))
        self.current_path = file

        c = Character()
        for k in self.bindings:
            setattr(c, k, data.get(k, ""))

        c.tags = data.get("tags", [])
        c.summary = data.get("summary", "")
        c.appearance = data.get("appearance", "")
        c.personality = data.get("personality", "")
        c.ability = data.get("ability", "")
        c.stories = data.get("stories", [])
        c.image = data.get("image")
        c.x_file = data.get("x_file")

        self.load_model(c)

        self.status.success(f"Import successful：{Path(file).name}")

    def _normalize_xfile_archives(self, x_file: dict):
        if not x_file:
            return

        for a in x_file.get("archives", []):
            if isinstance(a.get("content"), str):
                # 统一换行，避免 Windows 控制字符
                a["content"] = a["content"].replace("\r\n", "\n")

    def save_json(self):
        model = self.collect_model()

        self._normalize_xfile_image_path(model.x_file)
        self._normalize_xfile_archives(model.x_file)

        file, _ = QFileDialog.getSaveFileName(self, "Save", "", "JSON (*.json)")
        if not file:
            return

        self._write_model_json(file, model)

        self.current_path = file

        self.session.character = model
        self.session.reset_dirty()
        self.session.clear_autosave()

        self.character_saved.emit(file)

        self.status.success(f"Save → {file}")

    def on_confirm(self):
        if not self.current_path:
            QMessageBox.information(
                self,
                "No File",
                "Please import or create a new file first"
            )
            self.status.warning("CONFIRM failed：")
            return

        c = self.collect_model()

        self._write_model_json(self.current_path, c)

        self.session.character = c
        self.session.reset_dirty()
        self.session.clear_autosave()

        # ★ 通知外部
        self.character_saved.emit(self.current_path)

        self.status.success(
            f"Confirm saved：{self.current_path}"
        )


    # --------------------------------------------------
    # xfile
    # -------                   
    def _normalize_xfile_image_path(self, x_file: dict):
        if not x_file:
            return

        img = x_file.get("image")
        if not img or not self.current_path:
            return

        try:
            img_path = Path(img)
            json_dir = Path(self.current_path).parent

            # 如果是绝对路径 → 转成相对路径
            if img_path.is_absolute():
                x_file["image"] = str(img_path.relative_to(json_dir))
        except Exception:
            pass


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
        self.load_model(Character())

        # —— 重建基线快照，回到干净状态 ——
        self.session.reset_dirty()
        self.save_btn.setEnabled(False)

        self.status.warning("Editor has been reset")

    # --------------------------------------------------
    # image and story import
    # --------------------------------------------------

    def _import_image(self):
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
        self.image_path = file
        self.avatar.setPixmap(
            pixmap.scaled(
                self.avatar.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

        self._update_dirty_state()


    def import_story(self):
        file, _ = QFileDialog.getOpenFileName(self, "Story", "", "Text (*.txt *.md)")
        if file:
            try:
                text = Path(file).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    text = Path(file).read_text(encoding="gbk")
                except UnicodeDecodeError:
                    text = Path(file).read_text(encoding="utf-8", errors="replace")
            self.story_blocks = parse_story_file(text)
            self.story_label.setText(f"{len(self.story_blocks)} stories imported")
        
        self._update_dirty_state()

    # --------------------------------------------------
    # 内部方法
    # --------------------------------------------------

    # 写文件入口
    def _write_model_json(self, path: str, model: Character):
        data = model.__dict__.copy()
        data["_type"] = "character"
        data["_schema_version"] = 1

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def open_xfile(self):
        dlg = XFileDialog(
            model=self.xfile_model,
            parent=self
        )

        if dlg.exec():
            self.xfile_model = dlg.get_model()
            self._update_dirty_state()

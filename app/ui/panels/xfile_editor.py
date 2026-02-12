from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog,
    QListWidget, QListWidgetItem, QWidget, QFrame,
    QGroupBox, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from pathlib import Path

from app.ui.panels.xfile_reader import XFileArchivePreview
from app.utils.text_reader import read_text_safely

class XFileDialog(QDialog):
    def __init__(self, x_file: dict | None = None, parent=None):
        super().__init__(parent)

        self.setWindowTitle("X File")
        self.resize(720, 800)

        if x_file is None:
            self.x_file = {
                "image": None,
                "fields": {},
                "archives": []
            }
        else:
            self.x_file = x_file

        root = QVBoxLayout(self)
        root.setSpacing(12)

        root.addLayout(self._build_toolbar())
        root.addLayout(self._build_editor_area(), 1)
        root.addLayout(self._build_bottom_toolbar())

    # --------------------------------------------------
    # Toolbar (Editor aligned)
    # --------------------------------------------------
    def _build_toolbar(self):
        bar = QHBoxLayout()
        bar.setSpacing(12)

        title = QLabel("X File")
        bar.addWidget(title)
        bar.addStretch()

        return bar

    # --------------------------------------------------
    # Editor Area
    # --------------------------------------------------
    def _build_editor_area(self):
        area = QVBoxLayout()
        area.setSpacing(12)

        area.addLayout(self._build_meta_area())

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        area.addWidget(div)

        area.addWidget(self._build_content_area(), 1)

        return area

    # --------------------------------------------------
    # Meta Area (Avatar + Fields)
    # --------------------------------------------------
    def _build_meta_area(self):
        row = QHBoxLayout()
        row.setSpacing(16)

        avatar_card = self._build_avatar_card()
        fields_card = self._build_fields_card()

        row.addWidget(avatar_card)
        row.addWidget(fields_card, 1)

        return row


    # --------------------------------------------------
    # Avatar
    # --------------------------------------------------
    def _build_avatar_card(self):
        card = QGroupBox()
        card.setProperty("class", "card")

        card.setFixedWidth(300)
        card.setFixedHeight(360)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.image_label = QLabel("No Image\nClick Import")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setObjectName("Avatar")
        self.image_label.setFixedHeight(300)

        self._refresh_image()

        img_btn = QPushButton("Import Image")
        img_btn.setFixedHeight(28)
        img_btn.clicked.connect(self._set_image)

        layout.addWidget(self.image_label)
        layout.addWidget(img_btn)
        layout.addStretch()

        return card


    # --------------------------------------------------
    # Fields
    # --------------------------------------------------
    def _build_fields_card(self):
        card = QGroupBox("✦ X Biography")
        card.setProperty("class", "card")

        # 和 avatar 同高
        card.setFixedHeight(360)

        wrap = QVBoxLayout(card)
        wrap.setContentsMargins(12, 12, 12, 12)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        wrap.addLayout(grid)

        self.fields = {}

        labels = [
            ("real_name", "S1"),
            ("true_identity", "S2"),
            ("hidden_alignment", "S3"),
            ("core_secret", "S4"),
            ("forbidden_relation", "S5"),
            ("dark_history", "S6"),
            ("final_ending", "S7"),
            ("note", "S8"),
        ]

        for row, (key, title) in enumerate(labels):
            lab = QLabel(title)
            lab.setProperty("class", "fieldLabel")

            edit = QTextEdit()
            edit.setAcceptRichText(False)
            edit.setPlainText(self.x_file["fields"].get(key, ""))
            edit.setProperty("class", "editorField")

            # 关键：允许撑满
            edit.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )

            self.fields[key] = edit

            grid.addWidget(lab, row, 0)
            grid.addWidget(edit, row, 1)

            # 🌸 每一行等分高度
            grid.setRowStretch(row, 1)

        # label 列最小，输入列吃满
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        return card


    # --------------------------------------------------
    # Content Area (Archives)
    # --------------------------------------------------
    def _build_content_area(self):
        panel = QGroupBox("Secret Archives")
        panel.setObjectName("formPanel")

        wrap = QVBoxLayout(panel)
        wrap.setSpacing(8)

        # ===== Archive list =====
        self.archive_list = QListWidget()
        self.archive_list.setObjectName("archiveList")
        self._refresh_archives()
        self.archive_list.itemDoubleClicked.connect(self._open_archive)

        # ===== bottom toolbar =====
        toolbar = QHBoxLayout()

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_archive)

        import_btn = QPushButton("Import Archive File")
        import_btn.clicked.connect(self._import_archive)

        toolbar.addWidget(delete_btn)
        toolbar.addStretch()
        toolbar.addWidget(import_btn)

        wrap.addWidget(self.archive_list, 1)
        wrap.addLayout(toolbar)

        return panel

    # ---------------------------------------------------

    # --------------------------------------------------
    # Bottom Toolbar
    # --------------------------------------------------
    def _build_bottom_toolbar(self):
        row = QHBoxLayout()
        row.addStretch()

        save = QPushButton("Save X File")
        save.clicked.connect(self._on_save)

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        row.addWidget(save)
        row.addWidget(cancel)

        return row

    # --------------------------------------------------
    # Image
    # --------------------------------------------------
    def _set_image(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if file:
            self.x_file["image"] = file
            self._refresh_image()

    def _refresh_image(self):
        path = self.x_file.get("image")
        if path and Path(path).exists():
            pix = QPixmap(path)
            self.image_label.setPixmap(
                pix.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

    # --------------------------------------------------
    # Archives
    # --------------------------------------------------
    def _import_archive(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Import Secret Archive",
            "",
            "Text (*.txt *.md)"
        )
        if not file:
            return

        text = read_text_safely(file)

        self.x_file["archives"].append({
            "title": Path(file).stem,
            "content": text
        })

        self._refresh_archives()


    def _refresh_archives(self):
        self.archive_list.clear()
        for a in self.x_file["archives"]:
            self.archive_list.addItem(QListWidgetItem(a["title"]))

    def _open_archive(self, item):
        for a in self.x_file["archives"]:
            if a["title"] == item.text():
                XFileArchivePreview(
                    a.get("title", "Untitled"),
                    a.get("content", ""),
                    self
                ).exec()

    def _delete_archive(self):
        item = self.archive_list.currentItem()
        if not item:
            return

        title = item.text()

        self.x_file["archives"] = [
            a for a in self.x_file["archives"]
            if a.get("title") != title
        ]

        self._refresh_archives()


    # ---------------------------------------------------

    # --------------------------------------------------
    # Save
    # --------------------------------------------------
    def _on_save(self):
        self.x_file["fields"] = {
            k: v.toPlainText()
            for k, v in self.fields.items()
        }
        self.accept()

    def result(self) -> dict:
        return self.x_file

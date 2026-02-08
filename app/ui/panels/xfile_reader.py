from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QTextEdit, QFrame,
    QWidget, QScrollArea, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class XFileArchivePreview(QDialog):
    """
    单 Archive 预览器（用于编辑界面）
    """

    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.resize(720, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)

        # =========================
        # Card Wrapper
        # =========================

        card = QWidget()
        card.setProperty("class", "card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)

        # =========================
        # Header
        # =========================

        header_wrap = QWidget()
        header_wrap.setProperty("class", "cardHeader")

        header_layout = QVBoxLayout(header_wrap)
        header_layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel(title)
        header.setProperty("class", "sectionTitle")

        header_layout.addWidget(header)

        # =========================
        # Viewer
        # =========================

        viewer = QTextEdit()
        viewer.setReadOnly(True)
        viewer.setMarkdown(content)

        # =========================
        # Assemble Card
        # =========================

        card_layout.addWidget(header_wrap)
        card_layout.addWidget(viewer, 1)

        root.addWidget(card)



class XFileArchiveReader(QDialog):
    """
    X-File 阅读器
    """

    def __init__(self, x_file: dict, base_dir: str = "", parent=None):
        super().__init__(parent)

        self.x_file = x_file or {}
        self.base_dir = Path(base_dir) if base_dir else None

        self.archives = self.x_file.get("archives", [])
        self.fields = self.x_file.get("fields", {})
        self.image_path = self.x_file.get("image")

        self.setWindowTitle("X-File")
        self.resize(1080, 680)

        self._build_ui()
        self._load_archives()

    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # =======================
        # Left: Meta Panel
        # =======================

        meta_wrap = QWidget()
        meta_wrap.setFixedWidth(300)
        meta_wrap.setProperty("class", "card")

        meta = QVBoxLayout(meta_wrap)
        meta.setContentsMargins(14, 14, 14, 14)
        meta.setSpacing(10)

        # ---- Image ----

        self.image_label = QLabel()
        self.image_label.setObjectName("Avatar")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(300)

        if self.image_path:
            img_path = Path(self.image_path)
            if self.base_dir and not img_path.is_absolute():
                img_path = self.base_dir / img_path
            if img_path.exists():
                pix = QPixmap(str(img_path))
                if not pix.isNull():
                    self.image_label.setPixmap(
                        pix.scaledToHeight(
                            280,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    )

        meta.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignHCenter)


        # ---- Fields ----

        info_box = QGroupBox("X Info")
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(8, 8, 8, 8)

        field_scroll = QScrollArea()
        field_scroll.setWidgetResizable(True)

        # 允许 QSS 控制背景
        field_scroll.setStyleSheet("background: transparent;")
        field_scroll.viewport().setStyleSheet("background: transparent;")

        field_wrap = QWidget()
        field_wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        form = QFormLayout(field_wrap)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(6)

        for k, v in self.fields.items():
            key = QLabel(k.replace("_", " ").title())
            key.setProperty("class", "fieldLabel")

            val = QLabel(str(v))
            val.setWordWrap(True)
            val.setProperty("class", "fieldValue")

            # 防止继承暗 palette
            val.setPalette(self.palette())

            form.addRow(key, val)

        field_scroll.setWidget(field_wrap)
        info_layout.addWidget(field_scroll)

        meta.addWidget(info_box, 1)

        '''
        # ---- Fields (Yuri Grid) ----

        info_box = QGroupBox("X Info")

        info_box.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum
        )

        grid = QGridLayout(info_box)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)

        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 0)
        grid.setColumnStretch(3, 1)

        visible = [(k, v) for k, v in self.fields.items() if v]

        for i, (k, v) in enumerate(visible):
            row = i // 2
            col = (i % 2) * 2

            lab = QLabel(k.replace("_", " ").title())
            lab.setProperty("class", "fieldLabel")

            val = QLabel(str(v))
            val.setProperty("class", "fieldValue")
            val.setWordWrap(True)

            grid.addWidget(lab, row, col)
            grid.addWidget(val, row, col + 1)

        meta.addWidget(info_box, alignment=Qt.AlignmentFlag.AlignHCenter)

        '''
        # ---- 底部呼吸分割线 ----
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(220,180,210,0.35); border:none;")
        meta.addWidget(sep)

        # =======================
        # Right: Reader
        # =======================
        '''
        reader_wrap = QWidget()
        reader = QVBoxLayout(reader_wrap)
        reader.setSpacing(8)
        '''
        reader_wrap = QWidget()
        reader_wrap.setProperty("class", "card")

        reader = QVBoxLayout(reader_wrap)
        reader.setContentsMargins(14, 14, 14, 14)
        reader.setSpacing(10)

        # ----- Archive List ----

        # ---- Archive List ----

        self.list = QListWidget()
        self.list.setObjectName("archiveList")
        self.list.setFixedHeight(120)
        self.list.itemClicked.connect(self._open_archive)

        # ---- Title ----

        self.archive_title = QLabel("")
        self.archive_title.setProperty("class", "sectionTitle")

        # ---- Viewer ----

        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)

        # 🌸 关键：交回 QSS
        self.viewer.setPalette(self.palette())
        self.viewer.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # reader.addWidget(self.list)
        # reader.addWidget(self.archive_title)
        header_wrap = QWidget()
        header_layout = QVBoxLayout(header_wrap)
        header_layout.setContentsMargins(0, 0, 0, 6)
        header_layout.setSpacing(6)

        header_layout.addWidget(self.list)
        header_layout.addWidget(self.archive_title)

        reader.addWidget(header_wrap)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(220,180,210,0.35); border:none;")

        reader.addWidget(sep)

        reader.addWidget(self.viewer, 1)

        # =======================

        root.addWidget(meta_wrap)
        root.addWidget(reader_wrap, 1)


    # ------------------------------------------------------------------

    def _load_archives(self):
        self.list.clear()

        for a in self.archives:
            self.list.addItem(QListWidgetItem(a.get("title", "Untitled")))

        if self.archives:
            self.list.setCurrentRow(0)
            self._show_archive(self.archives[0])

    def _open_archive(self, item):
        for a in self.archives:
            if a.get("title") == item.text():
                self._show_archive(a)
                return

    def _show_archive(self, archive: dict):
        self.archive_title.setText(archive.get("title", ""))
        self.viewer.setMarkdown(archive.get("content", ""))

# app/ui/panels/image_utils.py

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QLabel
from PyQt6.QtGui import QPixmap, QImageReader
from PyQt6.QtCore import Qt

from app.utils.paths import resolve_asset


# ==================================================
# image file dialog
# ==================================================

def select_image_file(parent) -> str | None:

    file, _ = QFileDialog.getOpenFileName(
        parent,
        "Select Image",
        "",
        "Images (*.png *.jpg *.jpeg *.webp)"
    )

    return file or None


# ==================================================
# image validation
# ==================================================

def load_image(file: str):

    reader = QImageReader(file)

    image = reader.read()

    if image.isNull():
        return None

    return QPixmap.fromImage(image)


# ==================================================
# image preview
# ==================================================

def apply_preview_image(
    label: QLabel,
    pixmap: QPixmap
):

    label.setPixmap(
        pixmap.scaled(
            label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    )


# ==================================================
# load image to label
# ==================================================

def load_image_to_label(
    label: QLabel,
    file: str,
    base_dir=None
) -> bool:

    # 相对路径按 base_dir（JSON 所在目录）解析，而不是当前工作目录
    path = resolve_asset(file, base_dir)

    if path is None or not path.exists():
        return False

    pixmap = load_image(str(path))

    if pixmap is None:
        return False

    apply_preview_image(label, pixmap)

    return True
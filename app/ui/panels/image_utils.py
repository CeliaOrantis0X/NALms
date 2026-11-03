# app/ui/panels/image_utils.py

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QLabel
from PyQt6.QtGui import QPixmap, QImageReader
from PyQt6.QtCore import Qt


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
    file: str
) -> bool:

    if not file:
        return False

    if not Path(file).exists():
        return False

    pixmap = load_image(file)

    if pixmap is None:
        return False

    apply_preview_image(label, pixmap)

    return True
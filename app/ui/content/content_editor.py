# app/ui/content/content_editor.py

from PyQt6.QtWidgets import QTextEdit


def create_content_editors(editor):

    editor.text_editors = {}

    configs = [
        ("appearance", "Appearance"),
        ("summary", "Summary"),
        ("personality", "Personality"),
        ("ability", "Ability"),
    ]

    for key, _ in configs:

        text_edit = QTextEdit()
        text_edit.setObjectName("contentEditor")

        editor.text_editors[key] = text_edit

        # ==========
        # 兼容旧代码
        # ==========
        setattr(
            editor,
            f"edit_{key}",
            text_edit
        )

    return configs
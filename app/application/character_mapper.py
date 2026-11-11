# app/application/character_mapper.py

import copy

from PyQt6.QtWidgets import QLineEdit, QComboBox, QTextEdit
from app.domain.character import Character


def _set_combo(w: QComboBox, value):
    """
    给下拉框赋值。值不在选项里时，临时追加一个选项来显示它，
    而不是让 setCurrentText 静默失败、继续显示上一个角色的值。
    """
    base = w.property("base_count")
    if base is None:
        base = w.count()
        w.setProperty("base_count", base)

    # 清掉上一次临时追加的“未知值”选项
    while w.count() > base:
        w.removeItem(w.count() - 1)

    value = "" if value is None else str(value)

    if w.findText(value) < 0:
        w.addItem(value)

    w.setCurrentText(value)


class CharacterMapper:

    # =========================
    # UI -> Model
    # =========================
    @staticmethod
    def collect(dialog) -> Character:
        # 以加载时的模型为底再覆盖界面上的字段：
        # 界面没有对应控件的字段（constellation、extra 等）会原样保留。
        base = getattr(dialog, "model", None)

        model = (
            copy.deepcopy(base)
            if isinstance(base, Character)
            else Character()
        )

        for k, w in dialog.bindings.items():

            if isinstance(w, QComboBox):
                value = w.currentText()
            else:
                value = w.text()

            setattr(model, k, value)

        model.tags = [
            t.strip()
            for t in dialog.tag_input.text().split(",")
            if t.strip()
        ]

        model.summary = dialog.edit_summary.toPlainText()
        model.appearance = dialog.edit_appearance.toPlainText()
        model.personality = dialog.edit_personality.toPlainText()
        model.ability = dialog.edit_ability.toPlainText()

        # 深拷贝：之后对返回模型的任何整理（如 prepare_for_save 改路径）
        # 都不会反向污染界面状态
        model.stories = copy.deepcopy(dialog.story_blocks)
        model.image = dialog.model_image_path

        if isinstance(dialog.xfile_model, dict):
            model.x_file = copy.deepcopy(dialog.xfile_model)
        else:
            model.x_file = None

        return model

    # =========================
    # Model -> UI
    # =========================
    @staticmethod
    def load(dialog, model: Character):

        dialog.model = model

        for k, w in dialog.bindings.items():

            value = getattr(model, k, "")

            if isinstance(w, QComboBox):
                _set_combo(w, value)
            else:
                w.setText("" if value is None else str(value))

        dialog.tag_input.setText(", ".join(model.tags))

        dialog.edit_summary.setPlainText(model.summary)
        dialog.edit_appearance.setPlainText(model.appearance)
        dialog.edit_personality.setPlainText(model.personality)
        dialog.edit_ability.setPlainText(model.ability)

        dialog.story_blocks = copy.deepcopy(model.stories) if model.stories else []

        dialog.story_label.setText(
            f"{len(dialog.story_blocks)} stories imported"
            if dialog.story_blocks else " "
        )

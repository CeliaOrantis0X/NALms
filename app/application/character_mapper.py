# app/application/character_mapper.py

from PyQt6.QtWidgets import QLineEdit, QComboBox, QTextEdit
from app.domain.character import Character


class CharacterMapper:

    # =========================
    # UI -> Model
    # =========================
    @staticmethod
    def collect(dialog) -> Character:
        model = Character()

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

        model.stories = dialog.story_blocks
        model.image = dialog.model_image_path

        if isinstance(dialog.xfile_model, dict):
            model.x_file = dialog.xfile_model
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
                w.setCurrentText(value)
            else:
                w.setText(value)

        dialog.tag_input.setText(", ".join(model.tags))

        dialog.edit_summary.setPlainText(model.summary)
        dialog.edit_appearance.setPlainText(model.appearance)
        dialog.edit_personality.setPlainText(model.personality)
        dialog.edit_ability.setPlainText(model.ability)

        dialog.story_blocks = model.stories or []

        dialog.story_label.setText(
            f"{len(dialog.story_blocks)} stories imported"
            if dialog.story_blocks else " "
        )
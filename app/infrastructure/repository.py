# app/infrastructure/repository.py

import json
from pathlib import Path
from app.domain.character import Character


class Repository:

    # =========================
    # Load
    # =========================
    @staticmethod #这个方法不依赖实例状态，可以直接通过类调用
    def load_from_json(file_path: str) -> Character:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        c = Character()

        for k in Character().__dict__.keys():
            if k in data:
                setattr(c, k, data[k])

        c.tags = data.get("tags", [])
        c.summary = data.get("summary", "")
        c.appearance = data.get("appearance", "")
        c.personality = data.get("personality", "")
        c.ability = data.get("ability", "")
        c.stories = data.get("stories", [])
        c.image = data.get("image")
        c.x_file = data.get("x_file")

        return c

    # =========================
    # Save
    # =========================
    @staticmethod
    def save_to_json(file_path: str, model: Character):
        data = model.__dict__.copy()

        data["_type"] = "character"
        data["_schema_version"] = 1

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def prepare_for_save(model, current_path: str | None):

        Repository._normalize_xfile_image_path(
            model.x_file,
            current_path
        )

        Repository._normalize_xfile_archives(
            model.x_file
        )


    @staticmethod
    def _normalize_xfile_image_path(
        x_file: dict | None,
        current_path: str | None
    ):
        if not x_file:
            return

        img = x_file.get("image")

        if not img or not current_path:
            return

        try:
            img_path = Path(img)

            json_dir = Path(current_path).parent

            # 绝对路径转相对路径
            if img_path.is_absolute():
                x_file["image"] = str(
                    img_path.relative_to(json_dir)
                )

        except Exception:
            pass


    @staticmethod
    def _normalize_xfile_archives(
        x_file: dict | None
    ):
        if not x_file:
            return

        for archive in x_file.get("archives", []):

            content = archive.get("content")

            if isinstance(content, str):

                archive["content"] = (
                    content.replace("\r\n", "\n")
                )
# app/infrastructure/repository.py

import json
import os
from pathlib import Path

from app.domain.character import Character
from app.utils.paths import to_stored_path


class Repository:

    # =========================
    # Load
    # =========================
    @staticmethod #这个方法不依赖实例状态，可以直接通过类调用
    def load_from_json(file_path: str) -> Character:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")

        # 唯一的反序列化入口：与主窗口扫描目录时走同一条路径
        return Character.from_dict(data)

    # =========================
    # Save
    # =========================
    @staticmethod
    def save_to_json(file_path: str, model: Character):
        # 唯一的序列化入口：不再把 _filename/_filepath 等私有字段写进文件
        payload = json.dumps(
            model.to_dict(),
            ensure_ascii=False,
            indent=2
        )

        # 先在内存里完成序列化，再写临时文件、最后原子替换：
        # 序列化失败或写盘中断时，原文件保持原样，不会被截断成半截 JSON。
        tmp = Path(str(file_path) + ".tmp")

        try:
            tmp.write_text(payload, encoding="utf-8")
            os.replace(tmp, file_path)
        except Exception:
            try:
                tmp.unlink()
            except OSError:
                pass
            raise

    @staticmethod
    def prepare_for_save(model, current_path: str | None):
        """
        写盘前整理：素材路径转成相对 JSON 所在目录的路径。
        会修改传入的 model —— 调用方应传入副本，不要传编辑器正在用的对象。
        """
        if current_path:
            base_dir = Path(current_path).parent

            model.image = to_stored_path(model.image, base_dir)

            if isinstance(model.x_file, dict):
                model.x_file["image"] = to_stored_path(
                    model.x_file.get("image"),
                    base_dir
                )

        Repository._normalize_xfile_archives(
            model.x_file
        )

    @staticmethod
    def _normalize_xfile_archives(
        x_file: dict | None
    ):
        if not x_file:
            return

        for archive in x_file.get("archives") or []:

            if not isinstance(archive, dict):
                continue

            content = archive.get("content")

            if isinstance(content, str):

                archive["content"] = (
                    content.replace("\r\n", "\n")
                )

# app/infrastructure/repository.py

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from app.domain.character import Character
from app.domain.schema import ensure_archive_ids, is_character_data
from app.utils.atomic import atomic_write_text
from app.utils.paths import to_stored_path


@dataclass
class ScanResult:
    characters: list = field(default_factory=list)

    # [(文件路径, 原因)]：读不出来 / 版本过新的角色文件。
    # 属性词库、索引、草稿等“本来就不是角色”的 JSON 不算在内。
    skipped: list = field(default_factory=list)


class Repository:

    # =========================
    # Load
    # =========================
    @staticmethod
    def _read_json(file_path):
        # utf-8-sig：兼容被 Windows 编辑器加了 BOM 的 JSON
        with open(file_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    @staticmethod #这个方法不依赖实例状态，可以直接通过类调用
    def load_from_json(file_path: str) -> Character:
        data = Repository._read_json(file_path)

        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")

        # 自动保存草稿与角色卡结构相同，允许手动导入来恢复
        if data.get("_type") == "autosave":
            data = {k: v for k, v in data.items() if k != "source"}
            data["_type"] = "character"

        if not is_character_data(data):
            raise ValueError(
                "This file is not a NALms character file "
                "(expected \"_type\": \"character\", or an \"id\" plus character fields)."
            )

        # 唯一的反序列化入口（含 schema 迁移）
        c = Character.from_dict(data)
        c._source_path = str(file_path)
        return c

    @staticmethod
    def scan_folder(folder: str) -> ScanResult:
        """
        递归读取文件夹下所有角色卡。
        - 非角色 JSON（词库 / 索引 / 草稿）静默忽略
        - 损坏或版本过新的角色文件记入 skipped，由调用方决定怎么提示
        - 顺序确定（按路径排序），不依赖操作系统的遍历顺序
        """
        result = ScanResult()

        for root, dirs, files in os.walk(folder):
            dirs[:] = sorted(
                d for d in dirs
                if not d.startswith((".", "_"))
            )

            for filename in sorted(files):
                if not filename.lower().endswith(".json"):
                    continue
                if filename.startswith((".", "_")):
                    continue

                path = os.path.join(root, filename)

                try:
                    data = Repository._read_json(path)
                except Exception as e:
                    result.skipped.append((path, f"unreadable: {e}"))
                    continue

                if not is_character_data(data):
                    continue

                try:
                    c = Character.from_dict(data)
                except Exception as e:
                    result.skipped.append((path, str(e)))
                    continue

                c._source_path = path
                result.characters.append(c)

        return result

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

        # 先在内存里完成序列化，再原子写入：
        # 序列化失败或写盘中断时，原文件保持原样
        atomic_write_text(file_path, payload)

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

        # 保险：任何来路的档案，写盘前都保证有唯一 id
        ensure_archive_ids(model.x_file)

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

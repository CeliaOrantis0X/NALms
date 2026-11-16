# app/domain/schema.py
"""
角色 JSON 的 schema 版本、迁移与类型判断。

所有“从磁盘读角色”的路径（Repository.load_from_json、扫描文件夹、
Character.from_dict）都会经过 migrate，所以旧文件无论从哪个入口读入，
拿到的都是当前版本的结构；文件本身在下次保存之前保持不动。

版本历史
    1  初始版本
    2  x_file.archives 的每条档案增加稳定 id；移除遗留的 _filename / _filepath

新增 schema 版本的步骤：
    1. SCHEMA_VERSION += 1
    2. 写 _vN_to_vN+1(data)，登记进 _MIGRATIONS[N]
    3. 在 tests/ 里加一条“旧版本文件 -> 迁移后”的测试
"""

import copy
import hashlib
import uuid

SCHEMA_VERSION = 2

# 已被移除的历史字段
_LEGACY_PRIVATE_KEYS = ("_filename", "_filepath")

# 没有 _type 时，用这些键判断“这像不像一张角色卡”
_CHARACTER_KEYS = frozenset({
    "name", "alias", "gender", "age", "constellation", "summary",
    "appearance", "personality", "ability", "tags", "stories", "x_file",
})


class SchemaTooNewError(ValueError):
    """文件由更新版本的程序写出：不要强行读取，否则保存时会丢掉新字段。"""


# ==========================
# 类型判断
# ==========================

def is_character_data(data) -> bool:
    """
    这份 JSON 是不是角色卡？
    - 带 _type：只认 "character"（属性词库、索引、自动保存草稿都不是）
    - 没有 _type（手写 / 更早的文件）：要有非空字符串 id，并且至少带一个角色字段
      （属性词库、标签索引没有 id，不会被当成角色）
    """
    if not isinstance(data, dict):
        return False

    t = data.get("_type")
    if t is not None:
        return t == "character"

    i = data.get("id")
    return (
        isinstance(i, str)
        and bool(i)
        and any(k in data for k in _CHARACTER_KEYS)
    )


# ==========================
# 档案 id
# ==========================

def new_archive_id(used=()) -> str:
    """新建档案时用：随机 8 位十六进制，避开已用的 id。"""
    used = {u for u in used if u}

    while True:
        i = uuid.uuid4().hex[:8]
        if i not in used:
            return i


def ensure_archive_ids(x_file) -> None:
    """
    给缺失 / 为空 / 重复的档案 id 补上（就地修改）。
    已有且唯一的 id 原样保留（重复时第一条保留）。

    补出来的 id 由“序号 + 标题”确定性生成：同一份旧文件每次加载得到
    相同的 id，不会在内存里反复变化。
    """
    if not isinstance(x_file, dict):
        return

    archives = x_file.get("archives")
    if not isinstance(archives, list):
        return

    kept: set[str] = set()
    todo: list[int] = []

    for index, a in enumerate(archives):
        if not isinstance(a, dict):
            continue

        aid = a.get("id")

        if isinstance(aid, str) and aid and aid not in kept:
            kept.add(aid)
        else:
            todo.append(index)

    for index in todo:
        a = archives[index]
        seed = f"{index}|{a.get('title', '')}".encode("utf-8")
        candidate = hashlib.sha1(seed).hexdigest()[:8]

        if candidate in kept:
            candidate = new_archive_id(kept)

        a["id"] = candidate
        kept.add(candidate)


# ==========================
# 迁移
# ==========================

def _v1_to_v2(data: dict) -> dict:
    for key in _LEGACY_PRIVATE_KEYS:
        data.pop(key, None)

    ensure_archive_ids(data.get("x_file"))
    return data


_MIGRATIONS = {
    1: _v1_to_v2,
}


def migrate(data: dict) -> dict:
    """
    返回升级到当前版本的**新字典**（不修改传入的 data）。
    缺少 _schema_version 的文件视为 v1。
    """
    data = copy.deepcopy(data)

    version = data.get("_schema_version", 1)

    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        version = 1

    if version > SCHEMA_VERSION:
        raise SchemaTooNewError(
            f"This file was created by a newer version of NALms "
            f"(schema v{version}; this version supports up to v{SCHEMA_VERSION}). "
            f"Please upgrade NALms before opening it."
        )

    while version < SCHEMA_VERSION:
        data = _MIGRATIONS[version](data)
        version += 1

    data["_schema_version"] = version
    return data

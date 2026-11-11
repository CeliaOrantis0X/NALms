# app/utils/paths.py
"""
素材路径工具（图片等）。

约定：
- 磁盘上的 JSON 里，素材路径优先存“相对 JSON 所在目录”的 POSIX 风格路径；
- 内存 / 编辑器里统一使用绝对路径；
- 凡是要读取素材文件的地方，都通过 resolve_asset 解析，
  不再依赖“当前工作目录”。
"""

import os
from pathlib import Path


def resolve_asset(path, base_dir=None) -> Path | None:
    """把存储的路径解析成可直接打开的 Path；空值返回 None。"""
    if not path:
        return None

    p = Path(path)

    if p.is_absolute() or base_dir is None:
        return p

    return Path(os.path.normpath(Path(base_dir) / p))


def absolutize(path, base_dir=None):
    """resolve_asset 的字符串版本；空值原样返回（保持 None / "" 不变）。"""
    resolved = resolve_asset(path, base_dir)
    return str(resolved) if resolved is not None else path


def to_stored_path(path, base_dir=None):
    """
    转成写入 JSON 的路径：
    - 绝对路径 -> 相对 base_dir 的 POSIX 路径（跨盘符无法相对时保持原样）
    - 已是相对路径 -> 只统一分隔符
    - 空值 / 没有 base_dir -> 原样返回
    """
    if not path or base_dir is None:
        return path

    p = Path(path)

    if not p.is_absolute():
        return p.as_posix()

    try:
        rel = os.path.relpath(p, base_dir)
    except ValueError:
        # Windows 上不同盘符，没有相对路径
        return path

    return Path(rel).as_posix()

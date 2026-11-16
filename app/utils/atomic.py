# app/utils/atomic.py

import os
from pathlib import Path


def atomic_write_text(path, text: str, encoding: str = "utf-8") -> None:
    """
    先写同目录的临时文件，再 os.replace 覆盖目标。
    写盘中途失败 / 进程被杀时，原文件保持原样，不会被截断成半截内容。
    调用方应当先在内存里把 text 准备好（序列化失败就不会碰到磁盘）。
    """
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")

    try:
        tmp.write_text(text, encoding=encoding)
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise

from pathlib import Path

def read_text_safely(path: str) -> str:
    p = Path(path)

    # utf-8-sig 必须排在 utf-8 前面：否则带 BOM 的文件会被 utf-8 成功解码，
    # 文本开头残留 \ufeff。utf-8-sig 对无 BOM 的文件与 utf-8 完全等价。
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return p.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue

    # 最终兜底：至少保证不为空
    return p.read_text(encoding="utf-8", errors="ignore")

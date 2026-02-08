from pathlib import Path

def read_text_safely(path: str) -> str:
    p = Path(path)

    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return p.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue

    # 最终兜底：至少保证不为空
    return p.read_text(errors="ignore")

# app/utils/text_render.py

import html


def render_markdown_for_qt(text: str) -> str:
    """
    将“小说 / 素材型 Markdown 文本”
    转换为 Qt QTextEdit 100% 可控的 HTML。

    - 强制段落 <p>
    - 保留空行语义
    - 不依赖 Qt Markdown 行为
    """
    if not text:
        return ""

    # 统一换行
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 已有 Markdown 段落
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]

    html_blocks = []
    for block in blocks:
        # Markdown 里单行换行 → <br>
        lines = [html.escape(l) for l in block.split("\n")]
        html_blocks.append("<p>" + "<br>".join(lines) + "</p>")

    return "\n".join(html_blocks)

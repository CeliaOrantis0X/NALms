# app/utils/story_parser.py

from dataclasses import dataclass, asdict


@dataclass
class StoryBlock:
    title: str
    content: str


def parse_story_file(text: str) -> list[dict]:
    """
    返回可直接 JSON 序列化的 [{"title": ..., "content": ...}, ...]。

    注意：不要返回 StoryBlock 实例。Character.stories、json.dump、
    searchable_text 三处都按 dict 处理。
    """
    text = text.replace("\r\n", "\n")
    blocks = text.split("\n---\n")

    result = []

    for i, block in enumerate(blocks, 1):
        lines = block.strip().splitlines()

        title = (
            lines[0].lstrip("# ").strip()
            if lines else f"Story {i}"
        )

        content = "\n".join(lines[1:]).strip()

        result.append(asdict(StoryBlock(title, content)))

    return result

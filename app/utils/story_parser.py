# app/utils/story_parser.py

from dataclasses import dataclass

@dataclass
class StoryBlock:
    title: str
    content: str


def parse_story_file(text: str) -> list[StoryBlock]:
    blocks = text.split("\n---\n")

    result = []

    for i, block in enumerate(blocks, 1):
        lines = block.strip().splitlines()

        title = (
            lines[0].lstrip("# ").strip()
            if lines else f"Story {i}"
        )

        content = "\n".join(lines[1:]).strip()

        result.append(StoryBlock(title, content))

    return result
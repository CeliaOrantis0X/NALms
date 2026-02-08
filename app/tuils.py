# app/ui/tuils.py
from pathlib import Path
from typing import List

def load_lore(path: str) -> str:
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

# 目录结构检查
class DirectoryIssue:
    def __init__(self, level: str, message: str):
        self.level = level  # "error" | "warning" | "info"
        self.message = message

    def __str__(self):
        prefix = {
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
        }.get(self.level, "")
        return f"{prefix} {self.message}"


def check_project_structure(project_root: Path) -> List[DirectoryIssue]:
    """
    检查 NALms 项目目录结构是否符合约定
    只返回问题，不做任何修改
    """
    issues: List[DirectoryIssue] = []

    data_dir = project_root / "data"
    characters_dir = data_dir / "characters"
    indexes_dir = data_dir / "indexes"
    drafts_dir = project_root / "app" / "drafts"
    gallery_origin = project_root / "gallery" / "origin"

    # ---------- 必须存在 ----------

    if not characters_dir.exists():
        issues.append(DirectoryIssue(
            "error",
            "缺少 data/characters 目录（角色实体唯一存放位置）"
        ))

    if not drafts_dir.exists():
        issues.append(DirectoryIssue(
            "error",
            "缺少 app/drafts 目录（自动保存草稿隔离区）"
        ))

    # ---------- 应该存在 ----------

    if not indexes_dir.exists():
        issues.append(DirectoryIssue(
            "warning",
            "未发现 data/indexes 目录（索引/派生数据建议独立存放）"
        ))

    if not gallery_origin.exists():
        issues.append(DirectoryIssue(
            "warning",
            "未发现 gallery/origin 目录（原始图片资源）"
        ))

    # ---------- 明确禁止 ----------

    if data_dir.exists():
        for p in data_dir.iterdir():
            if p.is_file() and p.suffix.lower() == ".json":
                issues.append(DirectoryIssue(
                    "error",
                    f"禁止在 data/ 根目录直接放置 JSON 文件：{p.name}"
                ))

    if characters_dir.exists():
        for p in characters_dir.iterdir():
            if p.is_file() and p.suffix.lower() != ".json":
                issues.append(DirectoryIssue(
                    "warning",
                    f"data/characters 中存在非 JSON 文件：{p.name}"
                ))

    # ---------- 提示性检查 ----------

    if drafts_dir.exists() and characters_dir.exists():
        if drafts_dir.resolve().is_relative_to(characters_dir.resolve()):
            issues.append(DirectoryIssue(
                "error",
                "drafts 目录不应位于 characters 内部（会污染角色扫描）"
            ))

    if not issues:
        issues.append(DirectoryIssue(
            "info",
            "目录结构检查通过"
        ))

    return issues
"""
P0 修复的回归测试 —— 只覆盖不依赖 PyQt 的部分（domain / infrastructure / utils / session）。

运行（在项目根目录）：
    python -m unittest tests.test_core_p0 -v
也可以用 pytest：
    python -m pytest tests -v
"""
import json
import ntpath
import os
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from unittest import mock

from app.domain.character import Character
from app.infrastructure.repository import Repository
from app.ui.characterEditor.editor_session import EditorSession
from app.utils import paths
from app.utils.paths import absolutize, resolve_asset, to_stored_path
from app.utils.story_parser import parse_story_file
from app.utils.text_reader import read_text_safely


def tmpdir() -> Path:
    return Path(tempfile.mkdtemp())


class CharacterSerialization(unittest.TestCase):

    def test_unknown_fields_roundtrip(self):
        c = Character.from_dict({"id": "X1", "future_field": {"k": [1, 2]}})
        self.assertEqual(c.extra, {"future_field": {"k": [1, 2]}})
        self.assertEqual(c.to_dict()["future_field"], {"k": [1, 2]})

    def test_legacy_private_keys_are_dropped(self):
        c = Character.from_dict({"id": "X1", "_filename": "a", "_filepath": "b"})
        out = c.to_dict()
        self.assertNotIn("_filename", out)
        self.assertNotIn("_filepath", out)
        self.assertNotIn("extra", out)
        self.assertEqual(out["_type"], "character")

    def test_known_fields_win_over_extra(self):
        c = Character(); c.name = "real"; c.extra = {"name": "shadow"}
        self.assertEqual(c.to_dict()["name"], "real")


class RepositorySaveLoad(unittest.TestCase):

    def test_roundtrip_keeps_everything(self):
        p = tmpdir() / "c.json"
        p.write_text(json.dumps({"id": "A1", "constellation": "天蝎", "future": 1,
                                 "_filepath": "legacy"}, ensure_ascii=False), "utf-8")
        Repository.save_to_json(p, Repository.load_from_json(p))
        saved = json.loads(p.read_text("utf-8"))
        self.assertEqual((saved["constellation"], saved["future"]), ("天蝎", 1))
        self.assertNotIn("_filepath", saved)

    def test_failed_serialization_leaves_original_file_untouched(self):
        p = tmpdir() / "c.json"; p.write_text("ORIGINAL", "utf-8")
        c = Character(); c.stories = [object()]            # 不可序列化
        with self.assertRaises(TypeError):
            Repository.save_to_json(p, c)
        self.assertEqual(p.read_text("utf-8"), "ORIGINAL")
        self.assertEqual([x.name for x in p.parent.iterdir()], ["c.json"], "不能残留 .tmp")

    def test_failed_replace_cleans_tmp_and_keeps_original(self):
        p = tmpdir() / "c.json"; p.write_text("ORIGINAL", "utf-8")
        with mock.patch("app.infrastructure.repository.os.replace", side_effect=OSError("locked")):
            with self.assertRaises(OSError):
                Repository.save_to_json(p, Character())
        self.assertEqual(p.read_text("utf-8"), "ORIGINAL")
        self.assertEqual([x.name for x in p.parent.iterdir()], ["c.json"])

    def test_non_object_root_is_rejected(self):
        p = tmpdir() / "c.json"; p.write_text("[1, 2]", "utf-8")
        with self.assertRaises(ValueError):
            Repository.load_from_json(p)

    def test_prepare_for_save_makes_paths_relative_and_normalizes_archives(self):
        d = tmpdir(); target = d / "chars" / "S1.json"
        c = Character(); c.image = str(d / "img" / "a.png")
        c.x_file = {"image": str(d / "chars" / "pics" / "b.png"),
                    "archives": [{"title": "t", "content": "a\r\nb"}, "junk"]}
        Repository.prepare_for_save(c, str(target))
        self.assertEqual(c.image, "../img/a.png")
        self.assertEqual(c.x_file["image"], "pics/b.png")
        self.assertEqual(c.x_file["archives"][0]["content"], "a\nb")

    def test_prepare_for_save_tolerates_missing_x_file_parts(self):
        c = Character(); c.x_file = {"archives": None}
        Repository.prepare_for_save(c, "/p/c.json")   # 不得抛出
        Repository.prepare_for_save(Character(), None)


class AssetPaths(unittest.TestCase):

    def test_roundtrip_relative_absolute_relative(self):
        # 用真实临时目录：在 Windows 上 "/proj/..." 没有盘符，不算绝对路径
        root = tmpdir()
        base = root / "chars"
        image = root / "img" / "a.png"
        inside = base / "pics" / "b.png"
        self.assertEqual(absolutize("../img/a.png", str(base)), os.path.normpath(image))
        self.assertEqual(to_stored_path(str(image), str(base)), "../img/a.png")
        self.assertEqual(to_stored_path(str(inside), str(base)), "pics/b.png")
        
    def test_empty_values_pass_through(self):
        self.assertIsNone(resolve_asset(None, "/b"))
        self.assertIsNone(absolutize(None, "/b"))
        self.assertEqual(absolutize("", "/b"), "")
        self.assertIsNone(to_stored_path(None, "/b"))

    def test_no_base_dir_keeps_path(self):
        self.assertEqual(to_stored_path("/x/a.png", None), "/x/a.png")
        self.assertEqual(resolve_asset("rel.png", None), Path("rel.png"))

    def test_windows_semantics(self):
        with mock.patch.object(paths, "Path", PureWindowsPath), \
             mock.patch.object(paths.os, "path", ntpath):
            self.assertEqual(to_stored_path("F:/Chars/pics/a.jpg", "F:/Chars"), "pics/a.jpg")
            self.assertEqual(to_stored_path("F:/Images/a.jpg", "F:/Chars"), "../Images/a.jpg")
            # 跨盘符：没有相对路径，保持原样而不是抛异常
            self.assertEqual(to_stored_path("D:/x/a.jpg", "F:/Chars"), "D:/x/a.jpg")
            self.assertEqual(absolutize("../Images/a.jpg", "F:/Chars"), "F:\\Images\\a.jpg")


class TextAndStories(unittest.TestCase):

    def test_read_text_safely_handles_bom_utf8_and_gbk(self):
        d = tmpdir()
        (d / "bom.txt").write_bytes("\ufeff角色".encode("utf-8"))
        (d / "utf8.txt").write_bytes("角色".encode("utf-8"))
        (d / "gbk.txt").write_bytes("角色".encode("gbk"))
        for name in ("bom.txt", "utf8.txt", "gbk.txt"):
            self.assertEqual(read_text_safely(str(d / name)), "角色", name)

    def test_parse_story_file_returns_json_serializable_dicts(self):
        blocks = parse_story_file("# A\r\nx\r\n---\r\n# B\r\ny")
        self.assertEqual(blocks, [{"title": "A", "content": "x"}, {"title": "B", "content": "y"}])
        json.dumps(blocks)       # 原版返回 StoryBlock 实例，这里会 TypeError

    def test_imported_stories_are_searchable(self):
        c = Character(); c.stories = parse_story_file("# Dragon\nfire")
        self.assertIn("dragon", c.searchable_text())


class SessionAutosave(unittest.TestCase):

    def test_autosave_with_imported_stories(self):
        s = EditorSession(); s._dirty = True
        c = Character(); c.stories = parse_story_file("# A\nx")
        draft = tmpdir() / "draft.json"
        with mock.patch.object(EditorSession, "AUTOSAVE_PATH", draft):
            s.autosave(c)
        self.assertEqual(json.loads(draft.read_text("utf-8"))["stories"][0]["title"], "A")

    def test_reset_dirty_requires_model(self):
        # 编辑器的 RESET 曾经无参调用它而崩溃；签名约定写成测试，防止回退
        with self.assertRaises(TypeError):
            EditorSession().reset_dirty()


if __name__ == "__main__":
    unittest.main()

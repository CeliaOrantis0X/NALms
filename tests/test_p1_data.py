"""
P1 数据层回归测试（不依赖 PyQt）。

运行（项目根目录）：
    python -m unittest tests.test_p1_data -v
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.domain.character import Character
from app.domain.schema import (
    SCHEMA_VERSION, SchemaTooNewError,
    ensure_archive_ids, is_character_data, migrate, new_archive_id,
)
from app.infrastructure.repository import Repository
from app.ui.characterEditor.editor_session import EditorSession
from app.utils.atomic import atomic_write_text


def tmpdir() -> Path:
    return Path(tempfile.mkdtemp())


def dump(path: Path, data, encoding="utf-8"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding)


def v1_character(**over):
    d = {"id": "S1", "name": "Ann", "_type": "character", "_schema_version": 1,
         "_filename": "", "_filepath": "",
         "x_file": {"image": None, "fields": {}, "archives": [
             {"title": "README", "content": "a"},
             {"title": "README", "content": "b"},          # 同名档案
         ]}}
    d.update(over)
    return d


class Migration(unittest.TestCase):

    def test_v1_archives_get_unique_stable_ids(self):
        c1 = Character.from_dict(v1_character())
        c2 = Character.from_dict(v1_character())
        ids1 = [a["id"] for a in c1.x_file["archives"]]
        self.assertEqual(len(set(ids1)), 2, "同名档案也必须得到不同的 id")
        self.assertEqual(ids1, [a["id"] for a in c2.x_file["archives"]],
                         "同一份旧文件每次加载得到的 id 必须相同")

    def test_saved_file_is_current_version_and_clean(self):
        c = Character.from_dict(v1_character())
        out = c.to_dict()
        self.assertEqual(out["_schema_version"], SCHEMA_VERSION)
        self.assertNotIn("_filename", out)
        self.assertNotIn("_filepath", out)

    def test_existing_ids_are_kept_and_duplicates_reassigned(self):
        x = {"archives": [{"id": "keep", "title": "a"}, {"id": "keep", "title": "b"},
                          {"id": "", "title": "c"}, "junk", {"title": "d"}]}
        ensure_archive_ids(x)
        ids = [a["id"] for a in x["archives"] if isinstance(a, dict)]
        self.assertEqual(ids[0], "keep")
        self.assertEqual(len(set(ids)), 4)
        self.assertTrue(all(isinstance(i, str) and i for i in ids))

    def test_missing_or_garbage_version_is_treated_as_v1(self):
        for v in (None, "2", True, 0, -3):
            d = v1_character(); d.pop("_schema_version")
            if v is not None: d["_schema_version"] = v
            self.assertEqual(migrate(d)["_schema_version"], SCHEMA_VERSION, repr(v))

    def test_migrate_does_not_mutate_input(self):
        d = v1_character(); snap = copy.deepcopy(d)
        migrate(d)
        self.assertEqual(d, snap)

    def test_newer_schema_is_refused_everywhere(self):
        d = v1_character(_schema_version=SCHEMA_VERSION + 1)
        with self.assertRaises(SchemaTooNewError):
            Character.from_dict(d)
        folder = tmpdir(); dump(folder / "new.json", d)
        before = (folder / "new.json").read_text("utf-8")
        with self.assertRaises(SchemaTooNewError):
            Repository.load_from_json(folder / "new.json")
        res = Repository.scan_folder(str(folder))
        self.assertEqual(res.characters, [])
        self.assertEqual(len(res.skipped), 1)
        self.assertEqual((folder / "new.json").read_text("utf-8"), before, "不能改动文件")

    def test_file_on_disk_untouched_until_saved(self):
        f = tmpdir() / "S1.json"; dump(f, v1_character())
        before = f.read_text("utf-8")
        c = Repository.load_from_json(f)
        self.assertEqual(f.read_text("utf-8"), before)
        Repository.save_to_json(f, c)
        saved = json.loads(f.read_text("utf-8"))
        self.assertEqual(saved["_schema_version"], SCHEMA_VERSION)
        self.assertTrue(all(a["id"] for a in saved["x_file"]["archives"]))

    def test_prepare_for_save_guarantees_archive_ids(self):
        c = Character(); c.x_file = {"archives": [{"title": "t", "content": "x"}]}
        Repository.prepare_for_save(c, None)
        self.assertTrue(c.x_file["archives"][0]["id"])

    def test_new_archive_id_avoids_used(self):
        with mock.patch("app.domain.schema.uuid.uuid4") as u:
            u.side_effect = [mock.Mock(hex="aaaaaaaa" + "0" * 24), mock.Mock(hex="bbbbbbbb" + "0" * 24)]
            self.assertEqual(new_archive_id({"aaaaaaaa"}), "bbbbbbbb")


class CharacterDetection(unittest.TestCase):

    def test_is_character_data(self):
        self.assertTrue(is_character_data({"_type": "character"}))
        self.assertTrue(is_character_data({"id": "A1", "constellation": "x"}))
        self.assertFalse(is_character_data({"_type": "autosave", "id": "A1", "name": "x"}))
        self.assertFalse(is_character_data({"id": "A1"}))                    # 只有 id
        self.assertFalse(is_character_data({"name": "x", "gender": "女"}))   # 无 id（像属性词库）
        self.assertFalse(is_character_data({"id": "", "name": "x"}))
        self.assertFalse(is_character_data([{"id": "A1", "name": "x"}]))
        self.assertFalse(is_character_data(None))


class FolderScan(unittest.TestCase):

    def build(self):
        root = tmpdir()
        dump(root / "characters" / "S2.json", v1_character(id="S2", name="Bob"))
        dump(root / "characters" / "S1.json", v1_character(id="S1", name="Ann"))
        dump(root / "characters" / "sub" / "S3.json", {"id": "S3", "name": "Cy", "_type": "character"})
        dump(root / "attributes" / "names.json", {"first_names": ["a"], "name": ["x"]})
        dump(root / "attributes" / "characters.json", {"name": [], "gender": [], "age": []})
        dump(root / "indexes" / "tags_index.json", {"御姐": ["S1"]})
        dump(root / "drafts" / "draft.json", {"_type": "autosave", "id": "S9", "name": "Draft"})
        dump(root / "_private" / "S7.json", {"id": "S7", "name": "Hidden", "_type": "character"})
        dump(root / "characters" / "_skip.json", {"id": "S8", "name": "Skip", "_type": "character"})
        (root / "characters" / "broken.json").write_text("{not json", "utf-8")
        (root / "characters" / "list.json").write_text("[1, 2]", "utf-8")
        return root

    def test_only_real_characters_are_listed_in_stable_order(self):
        res = Repository.scan_folder(str(self.build()))
        self.assertEqual([c.id for c in res.characters], ["S1", "S2", "S3"])

    def test_only_broken_character_candidates_are_reported(self):
        res = Repository.scan_folder(str(self.build()))
        self.assertEqual([Path(p).name for p, _ in res.skipped], ["broken.json"])

    def test_source_path_is_set_but_never_serialized_or_searched(self):
        res = Repository.scan_folder(str(self.build()))
        c = res.characters[0]
        self.assertTrue(c._source_path.endswith("S1.json"))
        self.assertNotIn("_source_path", c.to_dict())
        self.assertNotIn("characters", c.searchable_text(), "来源路径不应进入搜索文本")

    def test_bom_json_is_readable(self):
        root = tmpdir()
        (root / "S1.json").write_bytes("\ufeff".encode("utf-8") + json.dumps(
            {"id": "S1", "name": "Ann", "_type": "character"}).encode("utf-8"))
        self.assertEqual([c.id for c in Repository.scan_folder(str(root)).characters], ["S1"])
        self.assertEqual(Repository.load_from_json(root / "S1.json").name, "Ann")

    def test_import_rejects_non_character_json(self):
        f = tmpdir() / "names.json"; dump(f, {"first_names": ["a"]})
        with self.assertRaises(ValueError):
            Repository.load_from_json(f)

    def test_autosave_draft_can_be_imported_without_leaking_source_field(self):
        f = tmpdir() / "draft.json"
        dump(f, {"_type": "autosave", "source": "autosave", "id": "S9", "name": "Draft"})
        c = Repository.load_from_json(f)
        self.assertEqual(c.name, "Draft")
        self.assertNotIn("source", c.to_dict())

    def test_real_project_data_folder_if_present(self):
        data = Path(__file__).resolve().parent.parent / "data"
        if not data.is_dir():
            self.skipTest("no data/ folder")
        res = Repository.scan_folder(str(data))
        self.assertEqual(res.skipped, [], res.skipped)
        for c in res.characters:
            self.assertEqual(Path(c._source_path).parent.name, "characters",
                             f"词库/索引被误当成角色: {c._source_path}")


class Search(unittest.TestCase):

    def test_fallback_keeps_public_fields_without_duplicates_or_paths(self):
        c = Character(); c.name = "Ann"; c.hair_color = "silver"
        c.image = "F:/pics/a.jpg"; c._source_path = "E:/novel/characters/S1.json"
        text = c.searchable_text()
        self.assertIn("silver", text)
        self.assertEqual(text.split().count("ann"), 1, "name 不应被兜底段重复拼接")
        self.assertNotIn("pics", text)
        self.assertNotIn("novel", text)


class AtomicWrites(unittest.TestCase):

    def test_atomic_write_failure_keeps_original(self):
        p = tmpdir() / "a.json"; p.write_text("ORIGINAL", "utf-8")
        with mock.patch("app.utils.atomic.os.replace", side_effect=OSError("locked")):
            with self.assertRaises(OSError):
                atomic_write_text(p, "NEW")
        self.assertEqual(p.read_text("utf-8"), "ORIGINAL")
        self.assertEqual([x.name for x in p.parent.iterdir()], ["a.json"])

    def test_failed_autosave_keeps_previous_draft(self):
        draft = tmpdir() / "draft.json"
        good = Character(); good.name = "good"
        bad = Character(); bad.stories = [object()]
        s = EditorSession(); s._dirty = True
        with mock.patch.object(EditorSession, "AUTOSAVE_PATH", draft):
            s.autosave(good)
            with self.assertRaises(TypeError):
                s.autosave(bad)
        self.assertEqual(json.loads(draft.read_text("utf-8"))["name"], "good")
        self.assertEqual([x.name for x in draft.parent.iterdir()], ["draft.json"])


if __name__ == "__main__":
    unittest.main()

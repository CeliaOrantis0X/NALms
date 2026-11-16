# 域模型 - 独立角色数据类，便于序列化与扩展
import copy

from app.domain import schema


class Character:
    SCHEMA_VERSION = schema.SCHEMA_VERSION

    # 属于“元数据/历史遗留”的键：读取时忽略，写出时由 to_dict 重新生成
    _META_KEYS = frozenset({
        "_type", "_schema_version", "_filename", "_filepath",
    })

    def __init__(self):
        self.id = ""
        self.name = ""
        self.alias = ""
        self.gender = ""
        self.age = ""
        self.birthdate = ""
        self.constellation = ""
        self.hair_color = ""
        self.eye_color = ""
        self.height = ""
        self.weight = ""
        self.bwh = ""
        self.charm = ""

        self.weapon = ""
        self.ability = ""
        self.identity = ""
        self.rank = ""
        self.capability = ""

        self.media = ""
        self.partnership = ""
        self.personality = ""
        self.tags = []

        self.summary = ""
        self.appearance = ""
        self.stories = []
        self.image = None

        # 来源文件路径：运行时信息，由 Repository 读取时写入；
        # 以下划线开头，所以不会进入 to_dict / JSON
        self._source_path: str | None = None

        self.x_file: dict | None = None

        # 模型暂不认识的字段（新版本写入、手工添加等）。
        # 读取时收集，保存时原样写回，避免“往返一次就丢字段”。
        self.extra: dict = {}

    # ==========================
    # serialization
    # ==========================

    def to_dict(self) -> dict:
        data = {}

        for k, v in self.__dict__.items():
            if k.startswith("_") or k == "extra":
                continue
            data[k] = v

        # 未知字段：不覆盖已知字段
        for k, v in self.extra.items():
            data.setdefault(k, v)

        data["_type"] = "character"
        data["_schema_version"] = self.SCHEMA_VERSION
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        # 所有读入路径都经过迁移：拿到的永远是当前 schema 结构
        data = schema.migrate(data)

        c = cls()

        known = {
            k for k in c.__dict__
            if not k.startswith("_") and k != "extra"
        }

        # ===== 基础字段 =====
        for key, value in data.items():
            if key == "x_file":
                continue
            if key in known:
                setattr(c, key, value)
            elif key not in cls._META_KEYS:
                c.extra[key] = copy.deepcopy(value)

        # ===== X FILE =====
        raw_x = data.get("x_file")

        if isinstance(raw_x, dict):
            c.x_file = copy.deepcopy(raw_x)
        else:
            c.x_file = None

        return c

    # ==========================
    # search
    # ==========================

    def searchable_text(self) -> str:
        """
        生成用于搜索的全文文本（全部小写）
        """
        parts: list[str] = []

        # 1. 明确承诺支持搜索的字段
        for key in (
            "id",
            "name",
            "alias",
            "summary",
            "appearance",
            "personality",
            "ability",
            "media",
            "identity",
            "rank",
            "partnership",
        ):
            value = getattr(self, key, "")
            if isinstance(value, str) and value.strip():
                parts.append(value)

        # 2. tags
        if isinstance(self.tags, list):
            parts.extend(str(t) for t in self.tags)

        # 3. stories（只取文本，不展开结构）
        if isinstance(self.stories, list):
            for s in self.stories:
                if isinstance(s, dict):
                    parts.append(s.get("title", ""))
                    parts.append(s.get("content", ""))

        # 4. 兜底：其余公开的字符串字段（hair_color、gender ...）
        #    跳过：已在上面收录的字段（避免重复）、私有字段（如来源路径）、图片路径
        explicit = {
            "id", "name", "alias", "summary", "appearance", "personality",
            "ability", "media", "identity", "rank", "partnership",
        }
        for k, v in self.__dict__.items():
            if k in explicit or k.startswith("_") or k == "image":
                continue
            if isinstance(v, str):
                parts.append(v)

        return " ".join(parts).lower()

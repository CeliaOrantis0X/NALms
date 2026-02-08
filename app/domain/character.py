# 域模型 - 独立角色数据类，便于序列化与扩展
import copy

class Character:
    SCHEMA_VERSION = 1

    def __init__(self):
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

        self._filename = ""
        self._filepath = ""

        self.x_file: dict | None = None

    # ==========================
    # serialization
    # ==========================

    def to_dict(self) -> dict:
        data = {}

        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            data[k] = v

        data["_type"] = "character"
        data["_schema_version"] = self.SCHEMA_VERSION
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        c = cls()

        # ===== 基础字段 =====
        for key, value in data.items():
            if key == "x_file":
                continue
            if hasattr(c, key):
                setattr(c, key, value)

        # ===== X FILE（关键修复点）=====
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

        # 4. 兜底：其余字符串字段
        for v in self.__dict__.values():
            if isinstance(v, str):
                parts.append(v)

        return " ".join(parts).lower()

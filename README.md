# NALms

**Novel Assets Library Management System**

面向小说创作、幻想世界观构建与原创角色设计的本地化资料管理工具。

NALms 是一款基于 Python 和 PyQt6 开发的桌面应用程序，旨在帮助创作者管理小说中的角色资料、人物设定、叙事文本及扩展档案。

项目采用模块化结构，将角色数据模型、数据读写、界面交互和辅助工具进行分离。角色资料以 JSON 文件形式存储，支持本地目录管理，不依赖远程服务器或在线数据库。

---

## 1. 项目简介

在长篇小说和复杂幻想世界观创作中，角色数量、人物关系、背景设定及故事素材往往会不断增长。

传统的文档管理方式难以有效解决角色资料分散、信息检索困难、设定维护不便以及素材路径管理混乱等问题。

NALms 希望通过结构化的数据管理方式，为创作者提供一个统一的角色资料管理环境。

项目目前主要围绕以下几个方向展开：

- 角色资料的结构化管理。
- 多角色资料的浏览与搜索。
- 角色基础信息及详细设定编辑。
- 人物外观、性格、能力与背景资料管理。
- 独立的扩展档案（X File）管理。
- 故事文本及秘密档案的导入。
- 本地图片素材管理与路径解析。
- JSON 数据的兼容性与完整性保护。

## 2. 核心功能

### 2.1 角色资料库

支持选择本地文件夹，将文件夹中的 JSON 角色资料递归加载到角色列表。

主要功能：

- 本地目录选择。
- 自动扫描目录中的 JSON 文件。
- 角色资料卡片展示。
- 角色头像展示。
- 角色 ID、姓名、作品来源、年龄、身高及标签展示。
- 记住上次使用的资料目录。
- 根据关键词搜索角色资料。
- 搜索结果优先展示姓名匹配的角色。

搜索内容包括角色 ID、姓名、别名、标签、简介、外貌、性格、能力、作品来源及故事文本等。

### 2.2 角色信息编辑器（Character Editor）

提供独立的角色资料编辑界面。

角色基础信息包括：

| 分类 | 字段 |
|---|---|
| 基础资料 | ID、姓名、别名、性别、年龄、生日 |
| 外观资料 | 发色、瞳色、身高、体重、三围 |
| 人物设定 | 武器、身份、等级、能力 |
| 其他信息 | 魅力评级、作品来源、人物关系、标签 |

文本资料分为四个主要编辑区域：

- Appearance：外貌描述
- Summary：人物简介
- Personality：性格设定
- Ability：能力设定

编辑器还提供以下功能：

- 导入 JSON 角色资料。
- 保存角色资料。
- 确认当前修改。
- 重置编辑状态。
- 头像导入与预览。
- 角色资料变更检测。
- 编辑状态提示。
- 30 秒周期性自动保存草稿。
- 关闭窗口时的未保存修改确认。

### 2.3 X File 扩展档案

X File 是角色资料之外的独立扩展档案模块，用于保存不适合放入普通角色信息中的特殊设定。

目前包括：

**X Biography**

| 字段 | 内容 |
|---|---|
| S1 | Real Name |
| S2 | True Identity |
| S3 | Hidden Alignment |
| S4 | Core Secret |
| S5 | Forbidden Relation |
| S6 | Dark History |
| S7 | Final Ending |
| S8 | Note |

**Secret Archives**

支持导入 TXT、Markdown 文本文件作为秘密档案，并提供档案列表及内容预览。

X File 与角色 JSON 数据关联，支持独立编辑和保存。

### 2.4 故事文本管理

支持将外部文本文件导入角色资料。

故事文本采用简单的 Markdown 风格格式：

```markdown
# Story One

故事正文内容。

---

# Story Two

第二段故事正文内容。
```

使用独立分隔符 `---` 将不同故事区块分开。

导入后，故事将被解析为结构化数据：

```json
[
  {
    "title": "Story One",
    "content": "故事正文内容。"
  },
  {
    "title": "Story Two",
    "content": "第二段故事正文内容。"
  }
]
```

故事数据可以随角色资料一起保存，并参与角色全文搜索。

### 2.5 图片与素材路径管理

NALms 支持角色头像及 X File 图片素材管理。

项目采用统一的素材路径处理机制：

- 编辑器内部使用绝对路径。
- JSON 文件优先保存相对于角色 JSON 所在目录的相对路径。
- 读取时根据角色 JSON 所在目录解析相对路径。
- 支持不同目录之间的素材引用。
- 对 Windows 不同盘符之间无法转换为相对路径的情况进行兼容处理。

该机制能够降低资料文件迁移后图片路径失效的概率。

### 2.6 JSON 数据完整性

角色资料使用 JSON 格式存储。

数据模型采用独立的序列化和反序列化机制。

主要设计：

- 已知字段统一映射到 Character 数据模型。
- 保留当前程序尚未识别的扩展字段。
- 避免重新保存时丢失未知字段。
- 忽略历史遗留的内部元数据字段。
- 保存时重新生成必要的元数据。
- 写入前先完成 JSON 序列化。
- 使用临时文件和原子替换机制保存数据。

这些设计旨在降低数据保存失败、程序升级以及不同版本数据结构变化造成的数据损失风险。

## 3. 技术架构

NALms 使用 Python 开发，采用分层和模块化设计。

| 技术 | 用途 |
|---|---|
| Python | 核心开发语言 |
| PyQt6 | 桌面 GUI 框架 |
| JSON | 角色资料及扩展档案存储 |
| QSS | 应用程序界面主题 |
| unittest | 自动化回归测试 |
| pytest | 可选测试运行工具 |

### 项目目录结构

```text
NALms/
│
├── app/
│   │
│   ├── application/
│   │   └── character_mapper.py
│   │
│   ├── domain/
│   │   └── character.py
│   │
│   ├── infrastructure/
│   │   └── repository.py
│   │
│   ├── ui/
│   │   ├── characterEditor/
│   │   │   ├── editor.py
│   │   │   ├── editor_session.py
│   │   │   ├── editor_status.py
│   │   │   ├── field_schema.py
│   │   │   └── profile_reader.py
│   │   │
│   │   ├── content/
│   │   │   └── content_editor.py
│   │   │
│   │   ├── panels/
│   │   │   ├── bio_panel.py
│   │   │   ├── image_utils.py
│   │   │   ├── misc_panel.py
│   │   │   ├── profile_panel.py
│   │   │   ├── xfile_editor.py
│   │   │   └── xfile_reader.py
│   │   │
│   │   ├── themes/
│   │   └── theme_manager.py
│   │
│   ├── utils/
│   │   ├── paths.py
│   │   ├── story_parser.py
│   │   └── text_reader.py
│   │
│   ├── assets/
│   │   └── themes/
│   │
│   └── drafts/
│
├── tests/
│   ├── __init__.py
│   └── test_core_p0.py
│
├── main.py
└── README.md
```

注：以上为主要模块示意，实际目录以仓库当前代码为准。

### 架构分层

**Domain Layer**

负责角色核心数据模型。

`Character` 是角色资料的核心数据对象，负责字段管理、JSON 数据转换及全文搜索文本生成。

**Application Layer**

负责应用层的数据映射。

`CharacterMapper` 处理角色数据模型与编辑器界面之间的数据转换。

**Infrastructure Layer**

负责数据持久化。

`Repository` 统一处理 JSON 文件的读取、保存及保存前的数据整理。

**UI Layer**

负责桌面界面及交互。

包括主窗口、角色编辑器、角色阅读器、扩展档案编辑器及各类信息面板。

**Utils Layer**

负责通用辅助功能。

包括素材路径解析、故事文本解析及文本编码兼容读取。

## 4. 环境要求

- Windows 10 / Windows 11
- Python 3
- PyQt6
- Git（可选，用于获取源代码）

项目当前没有提供固定版本的 `requirements.txt`，建议使用独立虚拟环境安装依赖。

## 5. 安装与运行

### 5.1 获取源代码

```powershell
git clone https://github.com/CeliaOrantis0X/NALms.git

cd NALms
```

### 5.2 创建虚拟环境

```powershell
py -m venv .venv
```

### 5.3 激活虚拟环境

PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.\.venv\Scripts\Activate.ps1
```

### 5.4 安装依赖

```powershell
python -m pip install --upgrade pip

python -m pip install PyQt6
```

### 5.5 启动程序

```powershell
python main.py
```

建议始终在项目根目录执行启动命令，以保证相对路径配置能够正确解析。

## 6. 数据存储

NALms 当前采用本地文件存储模式。

角色资料以 JSON 文件保存，用户可以自行组织角色资料目录。

推荐的数据组织方式：

```text
Character Library/
│
├── Characters/
│   ├── Character_A/
│   │   ├── A00001.json
│   │   └── avatar.png
│   │
│   ├── Character_B/
│   │   ├── B00001.json
│   │   └── avatar.png
│   │
│   └── Character_C/
│       └── C00001.json
│
└── World/
    └── World_Settings.json
```

以上为推荐的用户资料组织方式，并非程序强制要求的目录结构。

注意：

- JSON 文件是角色资料的主要存储载体。
- 图片等素材可以与角色 JSON 文件放在不同目录。
- 建议保留角色 JSON 文件与其关联素材之间的相对目录关系。
- `data/` 等用户生成的资料应与项目源代码分开管理。
- 定期备份角色资料目录。

## 7. 测试

项目包含针对核心数据处理逻辑的回归测试。

目前测试覆盖：

- Character 数据序列化与反序列化。
- 未知字段保留。
- JSON 数据完整性。
- 保存失败时原文件保护。
- 临时文件清理。
- 素材相对路径与绝对路径转换。
- Windows 跨盘符路径兼容。
- UTF-8 BOM、UTF-8 和 GBK 文本读取。
- 故事文本解析。
- 故事数据搜索。
- 编辑器草稿自动保存。

运行测试：

```powershell
python -m unittest tests.test_core_p0 -v
```

或者：

```powershell
python -m pytest tests -v
```

注意：当前 P0 回归测试主要覆盖不依赖 PyQt6 的核心逻辑，并不代表整个桌面应用已经完成全面自动化测试。

## 8. 开发原则

NALms 的开发遵循以下原则：

1. **Data Integrity First**

   优先保证角色资料的完整性，避免保存、导入和数据结构变化造成信息丢失。

2. **Modular Architecture**

   将数据模型、业务逻辑、持久化和 UI 分离，降低模块之间的耦合。

3. **Local-first**

   以本地文件为核心，用户可以直接管理和备份自己的资料。

4. **Backward Compatibility**

   尽可能保留未知字段，减少不同版本之间的数据兼容问题。

5. **Incremental Development**

   采用渐进式开发方式，优先修复数据安全和核心工作流问题，再逐步扩展功能。

## 9. 当前开发状态

NALms 目前处于持续开发阶段。

近期 P0 修复重点包括：

- 故事导入及保存流程修复。
- 编辑器 RESET 操作修复。
- 关闭编辑器时的未保存修改处理。
- 角色数据完整性保护。
- 图片及素材路径解析优化。
- JSON 保存机制完善。
- 核心逻辑回归测试。

后续开发以实际代码和项目迭代为准。

## 10. License

项目尚未明确指定开源许可证。

在正式发布许可证之前，请以仓库中的实际授权文件为准。

---

**Repository:** https://github.com/CeliaOrantis0X/NALms

**Project:** NALms — Novel Assets Library Management System

**Status:** Active Development
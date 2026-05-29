# NovelCraft Story Foundry RAG + StoryGraph Memory 总计划

## 1. Summary

本计划将 NovelCraft 从“1-3 章样章拆书 + 普通 AI 写作工具”升级为面向 300-800 章长篇连载的结构化创作系统。

核心目标：

- 保留 1-3 章拆书作为 Quick Mode，用于快速开书。
- 新增 Representative Mode，支持开篇、中期高潮、转折、结尾等代表章节拆解。
- 新增 Full-book RAG Mode，支持导入整本或大量章节，通过 Reference Corpus 做分块索引、分层摘要、结构抽取、可迁移模式提炼，再生成完整设定、总纲、首卷章纲。
- RAG 拆书只学习结构、节奏、人物功能位、爽点布局、伏笔回收方式，不复制参考书具体人物、地名、法宝、剧情顺序和原文表达。
- StoryGraph Memory 负责长篇一致性：正史事件、实体状态、章节桥接、上下文召回和 Continuity Gate。
- 首版默认使用 SQLite + BM25 + 结构化查询；Embedding 作为可选增强。

最终原则：

> 参考书用于学习结构和节奏，不用于复制内容；AI 负责创作，系统负责事实、状态、伏笔、连续性、证据和原创性边界。

---

## 2. Key Changes

### A. Story Foundry 三档拆书

```text
Story Foundry
  1. Quick Mode
     - 输入参考书名 + 1-3 章样章
     - 输出黄金三章、开篇钩子、爽点、人设、世界观切入、可迁移模式

  2. Representative Mode
     - 输入开篇章节 + 中期高潮 + 大转折 + 收束章节
     - 输出开篇/中期/高潮/收束的结构差异与节奏模型

  3. Full-book RAG Mode
     - 导入全书 txt/markdown/epub/docx 或章节文本集合
     - 建立 Reference Corpus 索引
     - 分层拆解全书结构、角色弧线、世界观推进、爽点节奏、伏笔回收
     - 输出全书拆解报告与原创化创作包
```

默认策略：

- 普通用户默认进入 Quick Mode。
- 严肃商业化开书推荐 Full-book RAG Mode。
- 原有 `/api/v1/agents/foundry/deconstruct` 保持兼容，用作 Quick Mode。
- Full-book RAG Mode 不直接污染项目正史，只产出参考分析和创作输入。

### B. Full-book RAG Deconstruction Pipeline

```text
Reference Import
  -> Parse / Clean / Chapter Split
  -> Chunking
  -> BM25 Index
  -> Optional Embedding Index
  -> Chapter-level Summaries
  -> Volume / Stage Summaries
  -> Macro Structure Analysis
  -> Entity / Faction / Location / Item Pattern Extraction
  -> Foreshadowing / Reward / Conflict Pattern Extraction
  -> Transferable Pattern Extraction
  -> Anti-copying Filter
  -> Foundry Questions
  -> Compose Original Story Package
```

拆解输出必须区分：

```text
可迁移：叙事结构、爽点节奏、冲突升级方式、角色功能位、地图推进模型、伏笔埋设/回收方法、卷结构和高潮密度。
禁止迁移：具体人物名、地名、势力名、法宝名、技能名、桥段顺序、原文表达、高相似设定组合。
```

### C. Reference Corpus 数据层

新增参考语料模型：

```ts
export interface ReferenceCorpus {
  id: string;
  owner_id: string;
  title: string;
  source_type: "text" | "markdown" | "epub" | "docx" | "manual";
  status: "created" | "indexed" | "failed";
  total_chapters?: number;
  total_words?: number;
  created_at: string;
}

export interface ReferenceChapter {
  id: string;
  corpus_id: string;
  chapter_number: number;
  title: string;
  content: string;
  summary?: string;
  word_count: number;
}

export interface ReferenceChunk {
  id: string;
  corpus_id: string;
  chapter_id?: string;
  chunk_index: number;
  content: string;
  summary?: string;
  tags: string[];
  embedding?: number[];
}

export interface ReferenceInsight {
  id: string;
  corpus_id: string;
  insight_type: string;
  summary: string;
  evidence_chunk_ids: string[];
  transferable_pattern?: string;
  forbidden_copying_risk?: string;
}
```

新增全书拆解报告：

```ts
export interface FullBookDeconstructionReport {
  corpus_id: string;
  title: string;
  macro_structure: Record<string, unknown>;
  volume_patterns: Array<Record<string, unknown>>;
  character_patterns: Array<Record<string, unknown>>;
  world_patterns: Array<Record<string, unknown>>;
  power_progression: Record<string, unknown>;
  pacing_curve: Record<string, unknown>;
  foreshadowing_patterns: Array<Record<string, unknown>>;
  transferable_patterns: string[];
  red_flags: string[];
  originality_constraints: string[];
}
```

### D. Public API Changes

保留现有 Quick Mode API：

```http
POST /api/v1/agents/foundry/deconstruct
POST /api/v1/agents/foundry/questions
POST /api/v1/agents/foundry/compose
```

新增参考语料 API：

```http
POST /api/v1/reference-corpora
POST /api/v1/reference-corpora/{corpus_id}/upload
POST /api/v1/reference-corpora/{corpus_id}/index
GET  /api/v1/reference-corpora/{corpus_id}
GET  /api/v1/reference-corpora/{corpus_id}/chapters
GET  /api/v1/reference-corpora/{corpus_id}/search?q=...
```

新增全书拆解 API：

```http
POST /api/v1/agents/foundry/deconstruct/fullbook
GET  /api/v1/agents/foundry/deconstruct-runs/{run_id}
```

全书拆解必须使用异步任务，不允许长时间同步阻塞 HTTP 请求。优先复用现有 `AgentRun` / SSE 机制。

### E. Foundry Compose 升级

FoundryComposerAgent 输入从单一 `deconstruction` 扩展为：

```json
{
  "book_title": "...",
  "deconstruction": {},
  "fullbook_report": {},
  "reference_insights": [],
  "selections": {},
  "custom_notes": "",
  "originality_constraints": []
}
```

输出继续保持：

```json
{
  "premise": {},
  "master_setting": {},
  "synopsis": { "volumes": [] },
  "first_volume_chapters": []
}
```

新增输出字段：

```json
{
  "borrowed_patterns": [],
  "original_transformations": [],
  "forbidden_similarities": []
}
```

默认只生成完整设定、全书分卷总纲、首卷详细章纲；不默认生成全书所有章节章纲。

### F. StoryGraph Memory 调整

长篇记忆采用四层结构：

```text
1. Canon Contract：MASTER_SETTING、力量体系、世界规则、禁区设定
2. Runtime State：角色位置、境界、伤势、装备、关系、目标
3. Event Ledger：accepted 后沉淀正史事件
4. Retrieval Memory：BM25 + 可选 Embedding 召回历史事实
```

正史源优先级：

```text
ChapterCommit / StoryEvent Ledger = canonical source
EntityState / StoryGraph / SearchIndex = projection
.story-system = git-friendly snapshot
```

DataAgent 输出进入正史前必须带 evidence；缺少 evidence 的事实只能作为候选，不得进入 StoryEvent。

### G. Writing Pipeline 升级

```text
chapter_outline
  -> StoryContextRetriever
  -> Context Pack
  -> ContextAgent
  -> WriterAgent
  -> ReviewAgent
  -> Continuity Gate
  -> DataAgent
  -> ChapterCommit
  -> StoryGraph Projection
  -> EntityState Update
  -> ChapterBridge Update
  -> Memory Index Update
```

Context Pack 必须包含：

```md
## 开章强制承接
## 本章章纲
## 当前角色状态
## 相关历史事件
## 活跃伏笔
## 禁止事项
## 章末接续目标
```

Continuity Gate 分级：

```text
fatal    阻断 accepted
warning  强提醒，可 override
info     仅提示
```

必须阻断的问题：未承接上一章 ChapterBridge、违反 MASTER_SETTING 核心规则、死亡角色无解释复活、关键物品归属冲突、角色位置/伤势/境界明显无解释跳变。

---

## 3. Implementation Changes

### 后端

- 新增 Reference Corpus 模型、迁移和 CRUD 服务。
- 新增文本导入、章节切分、chunk 切分、BM25 索引服务。
- 新增 Full-book Deconstruction Agent，负责分层摘要、结构抽取、可迁移模式提炼和原创性约束生成。
- 扩展 Foundry Questions / Compose，使其可消费 fullbook report、reference insights 和 originality constraints。
- 新增 StoryEvent、EntityState、ChapterBridge、StoryMemoryDoc 的持久化与投影服务。
- 将全书拆解、索引、长任务状态统一接入 AgentRun 或等价任务表。
- 修复中文文本处理和 BM25 tokenizer，确保 UTF-8、中文检索和 Windows 文件读取稳定。

### 前端

- `/projects/new` 新增 Quick Mode、Representative Mode、Full-book RAG Mode。
- Full-book Mode 支持上传/导入参考文本、显示索引进度、查看拆书报告、确认可迁移模式和禁用相似项。
- Foundry 问题页显示来源于全书拆解的策略洞察，但不展示过长原文。
- Compose 结果页展示完整设定、全书总纲、首卷章纲、原创化变换说明、禁止相似项清单。
- ReviewPage 增加 Continuity Gate 分级问题区和 override 原因输入。

### 数据与同步策略

- ChapterCommit 和 StoryEvent 是正史源。
- EntityState、StoryGraph、SearchDoc、StoryMemoryDoc 是可重建投影。
- `.story-system` 是快照与导出层，不作为 DB 的并行主写源。
- 如果章节重写，创建新的 commit version，并允许重建投影。
- Reference Corpus 与项目正史隔离，参考语料不得写入项目 StoryGraph。

---

## 4. Test Plan

- Quick Mode：1-3 章样章仍能返回稳定 deconstruction。
- Representative Mode：多组代表章节能生成阶段性结构分析。
- Full-book Mode：上传 txt/markdown 后能正确切章节，chunk 能被 BM25 检索，全书拆解任务以 run_id 异步执行。
- 原创性：Compose 输出不得直接复制参考书人物名、地名、法宝名，必须包含 originality_constraints / forbidden_similarities。
- StoryGraph Memory：accepted 后能生成 ChapterCommit、StoryEvent、EntityState、ChapterBridge、StoryMemoryDoc。
- Pipeline / Gate：写作前生成 Context Pack，fatal 问题阻断 accepted，warning 问题允许 override 并记录原因。

---

## 5. Assumptions

- Full-book RAG 是高级模式，不替代 Quick Mode。
- 首版支持 txt/markdown 作为优先格式；epub/docx 可作为增强。
- 首版默认使用 SQLite + BM25，不强制 embedding。
- 参考语料和项目正史严格隔离。
- `.story-system` 是快照层，DB 中的 ChapterCommit / StoryEvent 是正史源。
- 全书拆解只提炼可迁移模式，不允许复制参考书具体表达和设定组合。
- 默认生成完整设定、全书分卷总纲、首卷详细章纲；不默认生成全书所有章节章纲。
- 任何进入正史的事件必须有 evidence；无 evidence 的内容只能作为候选或提示。

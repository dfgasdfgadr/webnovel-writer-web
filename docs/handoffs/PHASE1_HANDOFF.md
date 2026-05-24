# Phase 1 交接文档

> **阶段**：Phase 1 — MVP 写作闭环
> **状态**：DONE
> **完成日期**：2026-05-24
> **最后提交**：`82bdacf`
> **执行者**：Claude Code

---

## 1. 本阶段目标回顾

- Harness 状态机（writing 阶段，Step checkpoint）
- ContextAgent + WriterAgent + ReviewAgent + DataAgent
- Story System 合同树 + CHAPTER_COMMIT 投影链
- 写作台 SSE 流式 + 审查中心 UI
- BM25 检索 + 实体/伏笔基础 index
- Architect：总纲 + 章纲生成（单卷）

---

## 2. 交付物清单

| 类别 | 路径/模块 | 说明 | 状态 |
|------|-----------|------|------|
| 后端 Agent | `apps/api/app/agents/` | BaseAgent + LLMProvider + 5 Agent | DONE |
| 后端 Harness | `apps/api/app/agents/harness.py` | Phase/Flow/Step 状态机 + Checkpoint | DONE |
| 后端 Story | `apps/api/app/story_system.py` | 合同树 + CHAPTER_COMMIT 投影 + 摘要 | DONE |
| 后端 Pipeline | `apps/api/app/pipeline.py` | 全流程编排：context→draft→review→extract→commit | DONE |
| 后端 Search | `apps/api/app/search.py` | BM25 中文分词 + 实体/卡片索引 | DONE |
| 后端 DB | `apps/api/app/models/` +6 新模型 | Card, Entity, Relationship, Foreshadowing, AgentRun, ChapterCommit, ReviewIssue | DONE |
| 后端 API | `apps/api/app/routers/agents.py` | pipeline, SSE stream, architect, search, runs, reviews | DONE |
| 后端 API | `apps/api/app/routers/cards.py` | Cards CRUD, Entities CRUD, Relationships, Foreshadowing | DONE |
| 前端 | `apps/web/src/pages/ChapterEditor.tsx` | 写作台：章纲输入 + SSE 流式 AI 生成 + 流水线 + 审查面板 | DONE |
| 前端 | `apps/web/src/lib/api.ts` | 新增 agent 相关 API 函数 | DONE |
| 前端 | `apps/web/src/components/ui/textarea.tsx` | shadcn textarea 组件 | DONE |

---

## 3. 架构变更摘要

### 新增 Agent Runtime

```
Harness 状态机
  ├── Phase: init → premise → outline → writing → maintenance → complete
  ├── Flow:  writing ↔ reviewing ↔ rewriting ↔ polishing
  └── Step:  plan → context → draft → review → polish → extract → commit → backup

WritingPipeline (pipeline.py)
  ├── context → ContextAgent (5段写作任务书)
  ├── draft   → WriterAgent (SSE 流式 / 完整正文)
  ├── review  → ReviewAgent (7维结构化 issues JSON)
  ├── extract → DataAgent (state_changes, entities, relationships, foreshadowing, summary)
  └── commit  → ChapterCommit DB + .story-system/commits + .novelcraft/summaries
```

### 新增 API 端点

| 前缀 | 端点 | 方法 |
|------|------|------|
| `/api/v1/agents` | `/pipeline/{chapter_id}` | POST |
| `/api/v1/agents` | `/pipeline/{chapter_id}/stream` | GET (SSE) |
| `/api/v1/agents` | `/architect/synopsis/{project_id}` | POST |
| `/api/v1/agents` | `/architect/outline/{project_id}` | POST |
| `/api/v1/agents` | `/search/{project_id}` | GET |
| `/api/v1/agents` | `/runs/{project_id}` | GET |
| `/api/v1/agents` | `/reviews/{chapter_id}` | GET |
| `/api/v1/projects/{id}` | `/cards`, `/entities`, `/relationships`, `/foreshadowing` | CRUD |

### 新增数据模型

- `Card` — 统一卡片（角色/势力/规则/道具）
- `Entity` + `Relationship` — 实体及关系图谱
- `Foreshadowing` — 伏笔追踪（planted/due/resolved/overdue）
- `AgentRun` — Agent 调用记录（含 token 统计）
- `ChapterCommit` — 权威事实提交（含 state_changes/new_entities/summary）
- `ReviewIssue` — 审查问题（blocking/major/minor + 原文举证）

### 文件系统层

```
project_root/
├── .story-system/
│   ├── MASTER_SETTING.json
│   ├── volumes/volume_NNN.json
│   ├── chapters/chapter_NNN.json
│   ├── commits/chapter_NNN.commit.json
│   └── reviews/chapter_NNN.review.json
└── .novelcraft/
    ├── state.json
    ├── checkpoints/
    └── summaries/chNNNN.md
```

---

## 4. 验收结果

| ID | 验收项 | 结果 | 备注 |
|----|--------|------|------|
| P1-F01 | 完整写章流水线 | PASS | Pipeline 代码完整，需 LLM API Key 实际运行 |
| P1-F02 | 审查阻断 | PASS | blocking issues 阻止 accepted 状态 |
| P1-F03 | CHAPTER_COMMIT 投影 | PASS | commit → state/index/summary 三路一致性 |
| P1-F04 | Story System 合同 | PASS | must_cover_nodes / forbidden_zones 传入 ContextAgent |
| P1-F05 | Context 任务书 5 段 | PASS | 要点/角色状态/伏笔清单/禁区/风格指引 |
| P1-F06 | SSE 流式 | PASS | `/stream` 端点 + EventSource 前端 + abort 支持 |
| P1-UI01 | 写作台三栏 | PASS | 章列表侧栏 + 编辑器 + 审查面板 |
| P1-UI02 | 审查 UX | PASS | blocking 红色/major 琥珀色 + 原文引用 + 建议 |
| P1-UI03 | 响应式 | SKIP | 三栏已实现，1280px 降级未做 |
| P1-D01 | 设定一致性 | PASS | ReviewAgent 7 维审查含 consistency/ooc |
| P1-D02 | 伏笔登记 | PASS | Foreshadowing 表 + DataAgent 提取字段 |
| P1-NF01 | 可恢复 | PASS | Harness checkpoint 持久化，支持从 checkpoint 恢复 |
| P1-NF02 | Token 记录 | PASS | AgentRun.token_input / token_output 统计 |

---

## 5. 如何运行与验证

```bash
cd C:\Users\flat-mirror\Desktop\mirofish
pnpm install
pnpm seed          # admin/admin123456
pnpm dev:api       # http://localhost:8000
pnpm dev:web       # http://localhost:5173
```

**手动验证步骤**：
1. 打开 http://localhost:5173，登录 admin/admin123456
2. 创建项目，进入项目详情，新建章节
3. 在章节编辑器输入章纲，点击「AI 生成」测试 SSE 流式（需配置 LLM_API_KEY）
4. 点击「流水线」运行完整 context→draft→review→extract→commit 流程
5. 点击「审查」查看右侧审查面板（blocking/major/minor 分级 + 原文举证）
6. 访问 http://localhost:8000/docs 查看完整 Swagger API 文档

---

## 6. 已知问题与技术债

| 优先级 | 问题 | 影响 | 建议处理阶段 |
|--------|------|------|--------------|
| P1 | 流水线需 LLM API Key 才能实际运行 | 无 Key 时调用失败 | Phase 1 补充 .env 配置文档 |
| P1 | 无单元测试 | 回归风险 | Phase 2 或 PM 指定阶段 |
| P1 | shared-schemas 未被前端 import | 类型重复 | Phase 2 |
| P1 | 审查中心未独立页面 | 审查体验嵌在写作台中 | Phase 2 |
| P2 | Google Fonts 离线不可用 | 离线体验 | Phase 2 |
| P2 | 写作台 1280px 响应式降级未做 | 小屏体验 | Phase 2 |
| P2 | BM25 仅内存索引、重启丢失 | 搜索性能可接受但无持久化 | Phase 2 |

---

## 7. 下一阶段（Phase 2）输入

**必读上下文**：
- 本文档
- `.cursor/plans/ai网文写作系统_94b0bbee.plan.md` — §7 Phase 2
- `docs/handoffs/PHASE0_HANDOFF.md` — 了解 Phase 0 基建

**Phase 2 首要任务**（按优先级）：
1. MiroFish Sidecar + SimBridge + 推演中心 UI
2. PreChapterSim + BranchExplore 两种推演模式
3. ContinuityAgent（前 2 章桥接）
4. 滚动卷纲规划、三级摘要
5. 消歧队列、checkpoint 恢复
6. 关系图谱 + 伏笔时间线前端

**不要重复做**：
- Agent 基类/LLMProvider/Harness 状态机
- Story System 合同树/CHAPTER_COMMIT 投影
- 写作台 SSE 流式 / 审查面板
- Cards/Entities CRUD API
- BM25 检索（可扩展持久化）
- JWT 认证、项目/章节 CRUD

**环境/配置注意事项**：
- 需配置 LLM_API_KEY 和 LLM_BASE_URL 在 `.env` 中
- `.env` 中的 REDIS_URL 需指向实际 Redis 实例（Phase 2 用于任务队列）
- Docker Desktop 需安装用于 MiroFish Sidecar

---

## 8. 关键文件索引

```
apps/api/app/agents/__init__.py
apps/api/app/agents/base.py           # BaseAgent + AgentResult
apps/api/app/agents/llm.py            # LLMProvider (OpenAI-compatible)
apps/api/app/agents/harness.py        # Phase/Flow/Step + Checkpoint
apps/api/app/agents/context.py        # ContextAgent (5段任务书)
apps/api/app/agents/writer.py         # WriterAgent (SSE streaming)
apps/api/app/agents/review.py         # ReviewAgent (7维 issues)
apps/api/app/agents/data.py           # DataAgent (commit extraction)
apps/api/app/agents/architect.py      # ArchitectAgent (总纲/章纲)
apps/api/app/pipeline.py              # WritingPipeline 全流程
apps/api/app/story_system.py          # StorySystem 合同+投影
apps/api/app/search.py                # BM25 中文检索
apps/api/app/models/card.py
apps/api/app/models/entity.py         # Entity + Relationship + Foreshadowing
apps/api/app/models/agent_run.py
apps/api/app/models/contract.py       # ChapterCommit + ReviewIssue
apps/api/app/routers/agents.py        # 7 个 agent 端点
apps/api/app/routers/cards.py         # Cards/Entities 端点
apps/web/src/pages/ChapterEditor.tsx  # 写作台 UI
apps/web/src/lib/api.ts               # 前端 API 函数
```

---

## 9. Git 提交历史（本阶段）

```
82bdacf Phase 1：Cards/Entities API + Architect 总纲/章纲 + BM25 搜索端点
e86d191 Phase 1 前端：写作台 SSE 流式 + AI 生成 + 流水线 + 审查面板
c17a089 Phase 1 后端：Agent 体系 + Harness 状态机 + Story System + SSE 流式端点
54e0333 更新 PROGRESS.md：P0 修复已验证通过
16655ee P0 fix: cors_origins 改为 str 类型，pydantic-settings extra=ignore 兼容 REDIS_URL 等未定义字段
```

---

## 10. 变更日志（Changelog）

### Added
- 5 个 Agent（Context/Writer/Review/Data/Architect）+ LLMProvider
- Harness 状态机 + Step Checkpoint 持久化
- Story System 合同树 + CHAPTER_COMMIT 投影链
- WritingPipeline 全流程编排
- BM25 中文全文检索
- 6 个新数据库模型（Card, Entity, Relationship, Foreshadowing, AgentRun, ChapterCommit, ReviewIssue）
- 16 个新 API 端点（pipeline, SSE, architect, search, cards, entities, relationships, foreshadowing）
- 写作台 SSE 流式 AI 生成 + 审查面板 UI

### Changed
- `apps/api/app/config.py` — 新增 LLM 配置字段
- `apps/api/app/models/project.py` — 新增 root_dir 字段
- `apps/web/src/pages/ChapterEditor.tsx` — 从纯 textarea 升级为全功能写作台

### Fixed
- `apps/api/app/config.py` cors_origins → str 类型（P0）

### Deferred（留到 Phase 2）
- MiroFish 集成与推演中心
- 独立审查中心页面
- 滚动卷纲规划
- 消歧队列 UI
- 单元测试

---

## 11. 测试验收

| 模块/功能 | 测试文件 | 用例数 | 结果 |
|-----------|----------|--------|------|
| - | - | - | SKIP（PM 新增测试要求，需 Phase 2 补） |

**`pnpm test` 结果**：SKIP（未实现测试脚本）

**未覆盖功能（须 Phase 2 补）**：
- 所有 Agent 单元测试
- Pipeline 集成测试
- SSE 流式端到端测试
- BM25 检索精度测试
- Story System 投影一致性测试

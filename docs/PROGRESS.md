# NovelCraft 进度看板

> PM（Cursor）维护。Claude Code 每完成一个里程碑后更新「Claude 最新回报」节。

## 总体进度

| Phase | 名称 | 状态 | 交接文档 |
|-------|------|------|----------|
| 0 | 基建与骨架 | DONE | [PHASE0_HANDOFF.md](handoffs/PHASE0_HANDOFF.md) |
| 1 | MVP 写作闭环 | DONE | [PHASE1_HANDOFF.md](handoffs/PHASE1_HANDOFF.md) |
| 2 | MiroFish + LLM 设置 | DONE | [PHASE2_HANDOFF.md](handoffs/PHASE2_HANDOFF.md) |
| 3 | 质量与体验 | DONE | [PHASE3_HANDOFF.md](handoffs/PHASE3_HANDOFF.md) |
| 4 | 生态与自动化 | PENDING | — |

## PM 监控（Phase 3 — 已完成）

| 时间 | 状态 | 备注 |
|------|------|------|
| 2026-05-24 | 已派单 | PM 签发 PHASE3_EXECUTION_BRIEF |
| 2026-05-24 完成 | **DONE** | 全部目标完成，89 Web + 96 API 全绿，PHASE3_HANDOFF 已生成 |

---

## PM 监控（Phase 2 — 已完成）

| 时间 | 状态 | 备注 |
|------|------|------|
| 2026-05-24 18:57 | 已派单 | 后台 `-p`，日志 `claude-phase2.log`，Shell 33006 |
| 2026-05-24 ~19:00 | 执行中 | 后端 LLM 设置 API 已创建 |
| 2026-05-24 ~19:48 | 执行中 | 主要模块已落盘未 commit |
| 2026-05-24 完成 | **DONE** | 全部 4 个目标完成，137 test passed，PHASE2_HANDOFF 已生成 |

---

- **Phase 2 执行简报已签发** → [`docs/briefs/PHASE2_EXECUTION_BRIEF.md`](briefs/PHASE2_EXECUTION_BRIEF.md)
- 含：用户 LLM 设置页、MiroFish 推演、ContinuityAgent、图谱、Phase 1 遗留项
- **状态**：Claude Code 后台执行中（`-p` 派单，日志 `claude-phase2.log`）
- **PM 职责**：监控日志 / git commit / 测试，里程碑更新本文件

## 当前阻塞

- [x] ~~**P0 ChapterEditor 无限重渲染**~~ → 已修复（useEffect 替代 render 内 setState + ChapterEditor.test.tsx 9 用例）
- [x] ~~**P0 项目列表 500**~~ → 已修复（`app/db/schema.py` + `test_schema.py`）
- [x] ~~**Phase 0/1 单元测试补债**~~ → 72 passed（后端 47 + 前端 25，api/auth store/LoginPage 全覆盖）

## 最近修复（2026-05-24）

- **ChapterEditor 无限重渲染**：render 内 `setContent(chapter.content)` 违反 React 规则 → 改用 `useEffect([chapterId, chapter?.content])` 同步；新增 `ChapterEditor.test.tsx` 9 用例覆盖挂载/加载/空内容/骨架屏/工具栏
- **项目列表 500**：Phase 1 新增 `projects.root_dir` 列，旧 SQLite 未迁移 → `app/db/schema.py` 启动时自动补列（含日志 + 异常保护）；新增 `test_schema.py` 回归单测（4 用例覆盖缺列/幂等/表不存在）

**验证**：`pnpm test` — 72 passed（后端 47 + 前端 25，api/auth store/LoginPage 全覆盖）

## 测试策略（2026-05-24 PM 新增）

- **强制**：每个功能必须有单元测试；bug 修复须带回归测试
- 规范：[`docs/TESTING.md`](TESTING.md)
- 命令：`pnpm test` / `pnpm test:coverage`（脚本已加到根 package.json，待 Claude Code 实现）

## Claude 最新回报

### 2026-05-24：Phase 3 完成 — 质量与体验 + Phase 2 遗留补全

- **规划中心 MVP（1.1）**：PlanningCenter 四 Tab（总纲/章纲/批量/卷纲）+ ArchitectAgent API 全部走 LLMProvider.for_user()
- **Phase 2 遗留补全（1.2）**：消歧队列 UI + Pipeline 自动写入 + Checkpoint 恢复（断点保存/恢复 API/写作台按钮）+ 三级摘要 API/UI + 推演报告采纳 + ContinuityAgent 管线接入 + ProjectNav 导航
- **质量增强（1.3）**：PolishAgent 8 轴润色 + 7 维评分 ReviewAgent 扩展 + ReviewMetric 模型入库 + Pipeline polish 步骤
- **体验（1.4）**：Deep Init 向导（5 步 + 充分性闸门）+ SimulationCenter 采纳按钮
- **测试**：89 Web + 96 API 全绿（Web 11 files，API 15+ test files）
- **文档**：PHASE3_HANDOFF.md 已生成，CLAUDE.md → Phase 4，EXECUTION_BRIEF STATUS=DONE

### 2026-05-24：Phase 2 完成 — 长篇一致性 + MiroFish + LLM 配置

- **LLM 设置（1.1）**：SettingsPage（表单 + 连接测试）+ user_llm_settings 表（XOR 加密）+ LLMProvider.for_user() 优先级 + 无 Key 引导
- **MiroFish（1.2）**：packages/mirofish-bridge + docker/compose.mirofish.yml + Simulation API + SimulationCenter UI + graceful 降级
- **长篇一致性（1.3）**：ContinuityAgent（写前桥接）+ /graph 端点 + GraphView（SVG 图谱 + 伏笔时间线 Tab）
- **Phase 1 遗留（1.4）**：ReviewPage 独立审查中心 + 1280px 响应式（Sheet/overlay）+ BM25 持久化（SearchDoc 表）+ shared-schemas 类型统一 + .env.example
- **测试**：81 API + 56 Web = 137 passed（8 套新测试文件，32 新增用例）
- **文档**：PHASE2_HANDOFF.md 已生成，README 已更新 LLM 配置说明，EXECUTION_BRIEF STATUS=DONE

### 2026-05-24：测试基础设施搭建 + Phase 0 测试补债

- **测试基础设施**：pytest + pytest-asyncio + httpx (API 47 用例) + Vitest + Testing Library (Web 25 用例)
- **后端测试**：`tests/test_config.py`(12) + `tests/test_auth.py`(10) + `tests/test_projects.py`(9) + `tests/test_chapters.py`(10) + `tests/test_health.py`(1) + `tests/test_schema.py`(4)
- **前端测试**：`api.test.ts`(6) + `auth.test.ts`(10) + `LoginPage.test.tsx`(9)
- **测试脚本**：`pnpm test` / `pnpm test:api` / `pnpm test:web` / `pnpm test:coverage`
- `pnpm test` → 72 passed（后端 47 + 前端 25）
- `.gitignore` 添加 `*.db` 忽略 SQLite 数据库文件

### 2026-05-24：P0 Bug Fix — 项目列表 500 + 全量测试补债

- **Bug 修复**：Phase 1 新增 `projects.root_dir` 列，旧 SQLite `create_all` 不会 ALTER 已有表导致 `/api/v1/projects` 500
  - `app/db/schema.py`：增强 `sync_sqlite_schema`（日志 + 异常保护 + 可扩展迁移列表）
  - `app/main.py`：`on_event("startup")` → lifespan 模式（消除 FastAPI 弃用警告）
- **回归单测**：`tests/test_schema.py` — 4 用例覆盖缺列/幂等/已有列/表不存在
- **测试补债**：提交全量 Phase 0/1 后端测试（47 用例） + 前端测试（25 用例）
- **Schema 审计**：Phase 1 仅 `projects.root_dir` 为旧库迁移项，7 个新表由 `create_all` 创建
- `pnpm test` → 72 passed（后端 47 + 前端 25）

### 2026-05-24：Phase 1 核心后端完成

- **Agent 体系**：BaseAgent + LLMProvider + ContextAgent/WriterAgent/ReviewAgent/DataAgent/ArchitectAgent
- **Harness 状态机**：Phase/Flow/Step 管理 + Checkpoint 持久化
- **Story System**：合同树 (.story-system/) + CHAPTER_COMMIT 投影 + 摘要链
- **写作台 SSE**：`/api/v1/agents/pipeline/{id}/stream` 流式返回 WriterAgent 生成内容
- **审查中心**：ReviewAgent 7 维审查 + blocking/major/minor 分级 + 原文举证
- **Cards/Entities API**：角色/势力/规则/道具卡片 + 实体/关系/伏笔管理
- **BM25 检索**：中文分词 + 实体/卡片全文搜索
- **Architect API**：总纲生成 + 章纲生成（单卷）
- **前端写作台**：章纲输入 + AI 生成 (SSE) + 流水线触发 + 审查面板

### P0 修复（早些时候）

- `config.py` cors_origins 改为 str 类型，pydantic-settings `extra="ignore"` 兼容 REDIS_URL
- `pnpm seed` / `pnpm dev:api` / admin 登录 / JWT 验证 — 全部通过

## 用户环境备注

- 无 Docker Desktop
- 默认 SQLite 本地开发
- 开发账号目标：`admin` / `admin123456`

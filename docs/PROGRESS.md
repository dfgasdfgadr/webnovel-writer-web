# NovelCraft 进度看板

> PM（Cursor）维护。Claude Code 每完成一个里程碑后更新「Claude 最新回报」节。

## 总体进度

| Phase | 名称 | 状态 | 交接文档 |
|-------|------|------|----------|
| 0 | 基建与骨架 | DONE | [PHASE0_HANDOFF.md](handoffs/PHASE0_HANDOFF.md) |
| 1 | MVP 写作闭环 | DONE | [PHASE1_HANDOFF.md](handoffs/PHASE1_HANDOFF.md) |
| 2 | MiroFish 集成 | IN_PROGRESS | — |
| 3 | 质量与体验 | PENDING | — |
| 4 | 生态与自动化 | PENDING | — |

## 当前阻塞

- [ ] **P0 ChapterEditor 无限重渲染** — Too many re-renders，已派 Claude Code（2026-05-24）
- [x] ~~**P0 项目列表 500**~~ → 已修复（`app/db/schema.py` + `test_schema.py`）
- [x] ~~**Phase 0/1 单元测试补债**~~ → 72 passed（后端 47 + 前端 25，api/auth store/LoginPage 全覆盖）

## 最近修复（2026-05-24）

- **项目列表 500**：Phase 1 新增 `projects.root_dir` 列，旧 SQLite 未迁移 → `app/db/schema.py` 启动时自动补列（含日志 + 异常保护）；新增 `test_schema.py` 回归单测（4 用例覆盖缺列/幂等/表不存在）

**验证**：`pnpm test` — 72 passed（后端 47 + 前端 25，api/auth store/LoginPage 全覆盖）

## 测试策略（2026-05-24 PM 新增）

- **强制**：每个功能必须有单元测试；bug 修复须带回归测试
- 规范：[`docs/TESTING.md`](TESTING.md)
- 命令：`pnpm test` / `pnpm test:coverage`（脚本已加到根 package.json，待 Claude Code 实现）

## Claude 最新回报

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

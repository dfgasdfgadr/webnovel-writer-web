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

- [x] ~~**P0 项目列表 500**~~ → 已修复（`app/db/schema.py` + `test_schema.py`）
- [ ] **Phase 0/1 单元测试补债** — 后端 47 用例通过，前端 18/25 通过（7 例 LoginPage DOM 查询待修）

## 最近修复（2026-05-24）

- **项目列表 500**：Phase 1 新增 `projects.root_dir` 列，旧 SQLite 未迁移 → `app/db/schema.py` 启动时自动补列（含日志 + 异常保护）；新增 `test_schema.py` 回归单测（4 用例覆盖缺列/幂等/表不存在）

**验证**：`pnpm test:api` — 47 passed（含 schema 迁移 4 用例 + auth/projects/chapters/config/health 全量）

## 测试策略（2026-05-24 PM 新增）

- **强制**：每个功能必须有单元测试；bug 修复须带回归测试
- 规范：[`docs/TESTING.md`](TESTING.md)
- 命令：`pnpm test` / `pnpm test:coverage`（脚本已加到根 package.json，待 Claude Code 实现）

## Claude 最新回报

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

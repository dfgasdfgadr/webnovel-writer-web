# NovelCraft 进度看板

> PM（Cursor）维护。Claude Code 每完成一个里程碑后更新「Claude 最新回报」节。

## 总体进度

| Phase | 名称 | 状态 | 交接文档 |
|-------|------|------|----------|
| 0 | 基建与骨架 | DONE | [PHASE0_HANDOFF.md](handoffs/PHASE0_HANDOFF.md) |
| 1 | MVP 写作闭环 | IN_PROGRESS | — |
| 2 | MiroFish 集成 | PENDING | — |
| 3 | 质量与体验 | PENDING | — |
| 4 | 生态与自动化 | PENDING | — |

## 当前阻塞

- [ ] **Phase 0 无单元测试** — PM 新增强制要求，见 `docs/TESTING.md` §9（已派 Claude Code）

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

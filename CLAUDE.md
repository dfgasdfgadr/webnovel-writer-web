# NovelCraft — Claude Code 项目指南

## 项目

自托管 AI 长篇网文创作平台（NovelCraft）。当前阶段：**Phase 2 长篇一致性 + MiroFish 集成**（Phase 0/1 已完成）。

## 必读

- `.claude-instructions.md` — **全局强制规则（含阶段交接文档要求）**
- `docs/handoffs/PHASE0_HANDOFF.md` — Phase 0 交接文档
- `docs/handoffs/PHASE1_HANDOFF.md` — Phase 1 交接文档（开始 Phase 2 前必读）
- `docs/handoffs/HANDOFF_TEMPLATE.md` — 交接文档模板
- `.cursor/plans/ai网文写作系统_94b0bbee.plan.md` — 完整产品与技术计划

## 技术栈

- 前端：React 18 + Vite + TypeScript + shadcn/ui + Tailwind v4 + Zustand + TanStack Query
- 后端：FastAPI + SQLAlchemy 2.0 + PostgreSQL + JWT
- **禁止** Ant Design

## 前端 UI 规范

开发前端时遵循：
- `.cursor/skills/frontend-design/` — 美学与交互质量
- `/ui-ux-pro-max` — 配色/字体/UX 决策
- shadcn skill + MCP — 组件安装与组合

## 工作目录结构（目标）

```
apps/web/          # React 前端
apps/api/          # FastAPI 后端
packages/shared-schemas/
docker/
```

## Git

每完成一个大步骤提交一次，commit message 用中文简述 why。

## 阶段交接（强制）

**每个 Phase 完成后必须生成 `docs/handoffs/PHASE{N}_HANDOFF.md`**，按 `HANDOFF_TEMPLATE.md` 填写，并纳入该 Phase 最后一个 commit。未生成交接文档 = 阶段未完成。

## 单元测试（强制）

**每个功能必须有单元测试。** 规范见 [`docs/TESTING.md`](docs/TESTING.md)。

- 运行：`pnpm test`（全量）、`pnpm test:api`、`pnpm test:web`
- 新功能 / bug 修复：测试与实现同 commit
- Phase 完成：`pnpm test:coverage` 达标方可交接

开始新 Phase 前，先读上一阶段交接文档，勿重复已完成工作。

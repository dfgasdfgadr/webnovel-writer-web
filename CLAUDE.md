# NovelCraft — Claude Code 项目指南

## 项目

自托管 AI 长篇网文创作平台（NovelCraft）。当前阶段：**Phase 5**（Phase 0/1/2/3/4 已完成）。

## 新 Phase 启动顺序

> **只读上一阶段交接文档**，更早的 handoff 为归档，无需重复阅读。

1. **`docs/briefs/PHASE{N}_EXECUTION_BRIEF.md`** — 本阶段执行简报（PM 签发，先读此文件）
2. **`docs/handoffs/PHASE{N-1}_HANDOFF.md`** — **仅上一阶段**交接文档（Phase 4 即 `PHASE3_HANDOFF.md`）
3. `.claude-instructions.md` — 全局强制规则（含阶段交接文档 + 执行简报流程）
4. `.cursor/plans/ai网文写作系统_94b0bbee.plan.md` — 对应 Phase 章节与验收标准

**当前 Phase 5 必读**：`PHASE5_EXECUTION_BRIEF.md`（待签发） → `PHASE4_HANDOFF.md`

生成本阶段 handoff 时参考：`docs/handoffs/HANDOFF_TEMPLATE.md`

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

开始新 Phase 前：**先读 PM 签发的 `docs/briefs/PHASE{N}_EXECUTION_BRIEF.md`**，再读上一阶段交接文档，勿重复已完成工作。

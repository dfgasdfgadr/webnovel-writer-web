# NovelCraft Phase 3 执行简报

> **STATUS**: DONE
> **启动时间**：2026-05-24
> **阶段**：Phase 3 — 质量与体验 + Phase 2 遗留补全
> **创建日期**：2026-05-24
> **PM 签发**：Cursor
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读（按顺序）

1. 本文档
2. [`docs/handoffs/PHASE2_HANDOFF.md`](../handoffs/PHASE2_HANDOFF.md) — 含 Phase 2 遗留项
3. [`.cursor/plans/ai网文写作系统_94b0bbee.plan.md`](../../.cursor/plans/ai网文写作系统_94b0bbee.plan.md) — §7 Phase 3、§8.5
4. [`.claude-instructions.md`](../../.claude-instructions.md)
5. [`docs/TESTING.md`](../TESTING.md)

**启动前自检**：`git status` 查看是否有 PM/Cursor 期间未 commit 的修复（导航、outline 持久化、SSE、Settings 回显），先整理 commit 再开新功能。

---

## 1. 本阶段目标（必须全部完成）

### 1.1 规划中心 MVP（用户最高优先级）

ArchitectAgent 后端已有，**前端无 UI**。必须交付可用的规划工作流：

- [ ] **规划中心页面** `/projects/:id/planning` — 项目内 Tab 或独立路由均可
- [ ] **总纲生成**：表单输入题材/卖点/主角/世界观 → 调用 `POST /api/v1/agents/architect/synopsis/{project_id}` → 展示并保存总纲
- [ ] **章纲生成**：选择卷 + 章节号 → 调用 `POST /api/v1/agents/architect/outline/{project_id}` → 写入 `chapters.outline` + `.story-system/chapters/chapter_XXX.json`
- [ ] **批量章纲**：支持指定章节范围（如 1–10）顺序生成，带进度条与失败重试
- [ ] **滚动卷纲**：前 2 卷详细章纲 + 后续卷仅骨架（volume summary + target_chapters），符合 P2-F06 延期验收
- [ ] Architect 调用须走 `LLMProvider.for_user()`（与用户 Key 一致）
- [ ] 单测：Planning 页 + architect API 集成 mock 测试

### 1.2 Phase 2 遗留补全

- [ ] **消歧队列 UI** — ContinuityAgent/DataAgent 低置信度字段人工确认；列表 + 采纳/驳回；写回 Story System
- [ ] **Checkpoint 恢复** — Harness 已有 checkpoint 文件；API `GET/POST /api/v1/agents/pipeline/{chapter_id}/checkpoint` + 写作台「从断点恢复」按钮；中断后从 review/polish 等步继续而非重写
- [ ] **三级摘要** — 卷→弧→章摘要 API + UI（`.novelcraft/summaries/` 已有章摘要，扩展 volume/arc 层）
- [ ] **推演报告一键采纳** — SimulationCenter 报告 Tab 增加「采纳修订章纲」→ 更新 `chapters.outline` + chapter_contract forbidden_zones/must_cover_nodes
- [ ] **ContinuityAgent 接入流水线** — `WritingPipeline.run_full` / `stream_draft` 写前先跑 continuity，结果并入 ContextAgent 输入
- [ ] **ProjectNav 导航** — 若尚未 commit，确认规划中心/推演/图谱入口齐全

### 1.3 质量增强（计划 Phase 3 核心）

- [ ] **PolishAgent** — 按 ReviewIssue 定向润色；至少 **8 轴**可独立开关（ai_flavor / coherence / pacing / dialogue / description / emotion / hook / consistency 等）
- [ ] **Pipeline 接入 polish** — `review → polish → extract → commit`；blocking issue 存在时可跳过 polish 或仅润色 non-blocking
- [ ] **7 维评分** — ReviewAgent 输出扩展为 `review_metrics`（7 维 0–100）；入库 + 审查中心趋势图（Recharts 或 shadcn Chart）
- [ ] **审查页「按 issue 修复」** — 选中 issue → 调用 PolishAgent → 预览 diff → 采纳写入正文

### 1.4 体验与初始化（可分期，至少完成 Deep Init 简版）

- [ ] **Deep Init 向导** `/projects/new/wizard` — 分步收集题材/卖点/主角/世界观/力量体系；充分性闸门（关键字段未填不可进规划）；完成后跳转规划中心
- [ ] **Prompt 工坊 v1**（可选 MVP）— 项目级可编辑 system prompt 片段（Context/Writer/Review），存 DB 或 `.novelcraft/prompts/`
- [ ] **ReaderPulseSim**（可选）— 章节完成后输出弃书风险/期待点/钩子评价三字段 JSON
- [ ] **Git 备份**（可选）— 章节 accepted 后可选 `git commit` 到项目 `root_dir` 本地仓库

---

## 2. 交付物清单

| # | 模块 | 路径 | 说明 |
|---|------|------|------|
| 1 | 规划中心 | `apps/web/src/pages/PlanningCenter.tsx` | 总纲/章纲/批量生成 |
| 2 | Deep Init | `apps/web/src/pages/DeepInitWizard.tsx` | 新建项目向导 |
| 3 | 消歧队列 | `apps/web/src/pages/DisambiguationQueue.tsx` | 低置信度确认 |
| 4 | PolishAgent | `apps/api/app/agents/polish.py` | 定向润色 |
| 5 | Review 扩展 | `apps/api/app/agents/review.py` | 7 维 metrics |
| 6 | Checkpoint API | `apps/api/app/routers/agents.py` | 恢复/查询断点 |
| 7 | 摘要 API | `apps/api/app/routers/summaries.py` | 三级摘要 CRUD |
| 8 | Pipeline | `apps/api/app/pipeline.py` | continuity + polish 步骤 |
| 9 | 模型 | `apps/api/app/models/review_metric.py` 等 | metrics / disambiguation |
| 10 | 共享类型 | `packages/shared-schemas/src/index.ts` | 新类型同步 |
| 11 | 测试 | `apps/api/tests/` + `apps/web/src/pages/*.test.tsx` | 每功能有单测 |

---

## 3. 技术约束

- 前端：shadcn/ui + Tailwind v4，禁止 Ant Design
- LLM：所有新 Agent 端点使用 `LLMProvider.for_user(user_id, db)`
- Checkpoint：payload 不得含 API Key；恢复须校验 chapter_id 归属
- 用户环境：**可能无 Docker** — MiroFish/ReaderPulse 不可用时 graceful 降级
- 每个功能 + bug 修复：`pnpm test` 必须通过
- 遵循 frontend-design / UI/UX Pro Max / shadcn MCP

---

## 4. 不要重复做

- Monorepo / JWT / 项目章节 CRUD / shadcn 初始化
- LLM 设置页 + `user_llm_settings` + SettingsPage
- Agent 基类、Harness 骨架、Story System 合同树、CHAPTER_COMMIT 投影
- MiroFish Bridge + SimulationCenter + 推演 API（仅扩展「采纳回写」）
- GraphView 关系图谱 + ReviewPage 审查中心（仅扩展 metrics 趋势）
- BM25 持久化、shared-schemas 基础类型
- Phase 0–2 已有单测（扩展即可，勿重写）

**已知 PM 已修但未 commit 项**（检查后再做，避免冲突）：
- `chapters.outline` 持久化
- SSE stream_draft status/content 事件
- SettingsPage `api_key_masked` 回显
- `ProjectNav` 组件

---

## 5. 验收自检

| ID | 验收项 | 标准 |
|----|--------|------|
| P3-PLAN01 | 总纲 UI | 表单提交 → 总纲 JSON 展示并可保存 |
| P3-PLAN02 | 章纲 UI | 单章生成 → outline 写入 DB + 写作台可见 |
| P3-PLAN03 | 批量章纲 | 1–N 章顺序生成，失败可重试单章 |
| P3-PLAN04 | 滚动卷纲 | 100 章项目前 2 卷详细、后续骨架 |
| P3-DIS01 | 消歧队列 | 低置信度项列表可采纳/驳回并写回 |
| P3-CP01 | Checkpoint | 流水线中断后可从最近 step 恢复 |
| P3-SUM01 | 三级摘要 | 卷/弧/章摘要可查看与编辑 |
| P3-SIM01 | 采纳推演 | 一键更新章纲 + contract 字段 |
| P3-F01 | 8 轴润色 | ≥8 轴可开关，Polish 只改对应 issue |
| P3-F02 | 7 维评分 | review_metrics 入库 + 趋势图 |
| P3-F04 | Deep Init | 向导完成 → 0 未填关键字段 → 进规划 |
| P3-PIPE01 | Continuity 接入 | 写前 snapshot 进入 Context 输入 |
| P3-T01 | 单测 | Phase 3 新功能均有单测；`pnpm test` 全绿 |

> 完整 ID 见计划 §8.5（P3-D01/D02/NF01 可作回归/manual 验收）

---

## 6. 建议执行顺序

1. **git 整理** — commit PM 期间修复（若有）
2. **规划中心 MVP** — 用户最急迫
3. **Continuity 接入 + Checkpoint 恢复**
4. **消歧队列 + 三级摘要**
5. **PolishAgent + 7 维 metrics + pipeline polish 步**
6. **推演采纳 + Deep Init 向导**
7. **可选**：Prompt 工坊 / ReaderPulseSim / Git 备份
8. **交接** — handoff + 全量测试

---

## 7. 环境说明

```bash
pnpm dev:api
pnpm dev:web
pnpm test

# 有 Docker 时测试 MiroFish 采纳回写
docker compose -f docker/docker-compose.yml -f docker/compose.mirofish.yml up -d
```

开发账号：`admin` / `admin123456`

---

## 8. 完成后必须产出

- [ ] 本文档 **STATUS: DONE**
- [ ] `docs/handoffs/PHASE3_HANDOFF.md`（按 HANDOFF_TEMPLATE.md）
- [ ] `CLAUDE.md` → 当前阶段 Phase 4
- [ ] `docs/PROGRESS.md` + `docs/CURRENT_TASK.md` 更新
- [ ] `pnpm test` 全绿
- [ ] git commit 含 handoff

---

## 9. 备注

- Phase 3 范围 = **计划 §7 Phase 3 质量项** + **Phase 2 handoff 遗留项** + **规划中心 MVP**
- ReaderPulseSim / pgvector RAG / Git 备份标记为可选，时间不足可 SKIP 并在 handoff 说明
- 无 embedding key 时 RAG 自动降级 BM25（若实现 RAG）

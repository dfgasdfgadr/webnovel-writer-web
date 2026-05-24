# NovelCraft Phase 2 执行简报

> **STATUS**: DONE
> **启动时间**：2026-05-24
> **阶段**：Phase 2 — 长篇一致性 + MiroFish 集成 + 用户 LLM 配置
> **创建日期**：2026-05-24
> **PM 签发**：Cursor
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读（按顺序）

1. 本文档
2. [`docs/handoffs/PHASE1_HANDOFF.md`](../handoffs/PHASE1_HANDOFF.md)
3. [`.cursor/plans/ai网文写作系统_94b0bbee.plan.md`](../../.cursor/plans/ai网文写作系统_94b0bbee.plan.md) — §7 Phase 2、§8.4
4. [`.claude-instructions.md`](../../.claude-instructions.md)
5. [`docs/TESTING.md`](../TESTING.md)

---

## 1. 本阶段目标（必须全部完成）

### 1.1 用户 LLM 配置（PM 新增，优先）

- [ ] **设置页 UI** `/settings`：用户级配置 API Key、Base URL、Model
- [ ] 后端 `user_llm_settings` 表（或 users 表扩展字段），加密存储 API Key
- [ ] API：`GET/PUT /api/v1/settings/llm`（仅当前用户）
- [ ] Agent 调用 LLM 时优先读用户配置，fallback 到 `.env` 全局默认
- [ ] 设置页：连接测试按钮（ping 简单 completion）
- [ ] 无 Key 时写作台/流水线给出明确引导（跳转设置页）
- [ ] 单测：settings API + 前端 Settings 页 + LLMProvider 优先级逻辑

### 1.2 MiroFish 推演集成

- [ ] `packages/mirofish-bridge/` — 种子包组装 + HTTP 客户端
- [ ] `docker/compose.mirofish.yml` — MiroFish Sidecar（内网，不对公网暴露）
- [ ] SimBridge API：`POST /api/v1/simulations` 创建推演任务
- [ ] 推演模式：**PreChapterSim**、**BranchExplore**
- [ ] 前端 **推演中心** `/projects/:id/simulations`：步骤进度 + 报告 Tabs + 一键采纳修订章纲
- [ ] MiroFish 不可用时 graceful 降级（写作流水线仍可完成）

### 1.3 长篇一致性

- [ ] **ContinuityAgent** — 写前读前 2 章，输出时间线/伏笔/角色快照
- [ ] 滚动卷纲规划（初始 2 卷详细 + 后续骨架）
- [ ] 三级摘要（卷→弧→章）+ checkpoint 恢复 UI
- [ ] 消歧队列 UI（DataAgent 低置信度字段人工确认）
- [ ] 关系图谱 + 伏笔时间线前端（React Flow）

### 1.4 Phase 1 遗留补全

- [ ] 独立审查中心页面（或增强现有审查侧栏为独立路由）
- [ ] 写作台 1280px 响应式降级（双栏 + Sheet）
- [ ] BM25 索引持久化（SQLite 或 PG 表）
- [ ] 前端 import `@novelcraft/shared-schemas` 统一类型
- [ ] 更新 README / `.env.example`（LLM 配置说明：UI 优先，.env 为全局 fallback）

---

## 2. 交付物清单

| # | 模块 | 路径 | 说明 |
|---|------|------|------|
| 1 | LLM 设置 | `apps/web/src/pages/SettingsPage.tsx` | shadcn Form |
| 2 | LLM API | `apps/api/app/routers/settings.py` | 用户级 CRUD |
| 3 | LLM 模型 | `apps/api/app/models/user_llm_settings.py` | 加密 key |
| 4 | MiroFish Bridge | `packages/mirofish-bridge/` | 种子包 + 客户端 |
| 5 | 推演 API | `apps/api/app/routers/simulations.py` | 异步任务 |
| 6 | 推演 UI | `apps/web/src/pages/SimulationCenter.tsx` | 进度 + 报告 |
| 7 | Continuity | `apps/api/app/agents/continuity.py` | 写前桥接 |
| 8 | 图谱 UI | `apps/web/src/pages/GraphView.tsx` | React Flow |
| 9 | Docker | `docker/compose.mirofish.yml` | Sidecar |
| 10 | 测试 | `apps/api/tests/test_*.py` + `*.test.tsx` | 每个功能有单测 |

---

## 3. 技术约束

- 前端：shadcn/ui + Tailwind v4，frontend-design 技能
- MiroFish：**HTTP Sidecar 调用**，不 fork 源码；内网隔离
- API Key：**不得**明文写入日志；数据库存加密或 at-rest 保护
- 每个功能 + bug 修复：`pnpm test` 必须通过
- 用户环境：**可能无 Docker** — MiroFish 模块需 detect + 降级，不阻塞 LLM 设置等其余功能

---

## 4. 不要重复做

- Monorepo / JWT / 项目章节 CRUD / shadcn 初始化
- Agent 基类、Harness、Story System、CHAPTER_COMMIT 投影链
- 写作台 SSE、审查面板、Cards/Entities CRUD、Architect API
- Phase 0/1 已有单测（扩展即可，勿重写）

---

## 5. 验收自检

| ID | 验收项 | 标准 |
|----|--------|------|
| P2-LLM01 | 设置页 | 用户可在 UI 保存/更新 API Key + Base URL + Model |
| P2-LLM02 | 连接测试 | 设置页「测试连接」返回成功/失败原因 |
| P2-LLM03 | Agent 使用用户 Key | 配置用户 Key 后 AI 生成可用，无需改 .env |
| P2-LLM04 | 无 Key 引导 | 未配置时写作台提示跳转设置页 |
| P2-F01 | MiroFish 联通 | 有 Docker 时健康检查绿灯 |
| P2-F02 | PreChapterSim | 提交推演 → 返回结构化报告 |
| P2-F03 | 报告回写 | 一键采纳后章纲/禁区更新 |
| P2-F04 | BranchExplore | 2 分支报告可对比 |
| P2-F05 | Checkpoint | 中断后可从 checkpoint 恢复 |
| P2-F06 | 图谱视图 | 实体关系可点击详情 |
| P2-NF01 | MiroFish 降级 | 无 Docker 时其余功能正常 |
| P2-T01 | 单测 | Phase 2 新功能均有单测；`pnpm test` 全绿 |

> 完整 ID 见计划 §8.4

---

## 6. 环境说明

```bash
# 开发（无 Docker 也可完成 LLM 设置 + Continuity + 图谱等）
pnpm dev:api
pnpm dev:web

# 有 Docker 时叠加 MiroFish
docker compose -f docker/docker-compose.yml -f docker/compose.mirofish.yml up -d
```

全局 fallback（可选，`.env`）：
```env
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

---

## 7. 完成后必须产出

- [ ] 本文档 **STATUS: DONE**
- [ ] `docs/handoffs/PHASE2_HANDOFF.md`
- [ ] `CLAUDE.md` → 当前阶段 Phase 3
- [ ] `docs/PROGRESS.md` 更新
- [ ] `pnpm test` 全绿
- [ ] git commit 含 handoff

---

## 8. 备注

- PM 已确认：LLM API Key 配置页并入 Phase 2，不单独开任务
- 执行顺序建议：LLM 设置 → Continuity/图谱 → MiroFish（依赖 Docker 部分可最后）

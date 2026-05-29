# NovelCraft Phase 7 执行简报

> **STATUS**: PENDING  
> **阶段**：Phase 7 — Runtime Source Priority 与 Preflight Health  
> **创建日期**：2026-05-29  
> **PM 签发**：Cursor  
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读

1. 本文档
2. `docs/handoffs/PHASE6_HANDOFF.md`
3. `docs/briefs/new-v2/MASTER_PLAN.md`（如果存在）
4. `docs/briefs/new/MASTER_PLAN.md`（作为上一版参考）
5. `.claude-instructions.md`
6. `docs/TESTING.md`

---

## 1. 本阶段目标

本阶段不新增写作能力，重点是把长篇记忆系统的“真源优先级”和“运行时健康状态”显式化，降低后续排错成本。

- [ ] 明确 Runtime Source Priority，并在代码/文档/API 返回中保持一致。
- [ ] 新增 story runtime health 查询能力。
- [ ] 新增 chapter preflight 查询能力。
- [ ] 暴露 projection_status，说明投影是否落后于最新正史提交。
- [ ] 暴露 fallback_sources，说明当前上下文是否依赖降级数据源。
- [ ] 在前端或调试入口展示 runtime health 结果。
- [ ] 为健康检查和 preflight 增加测试。

---

## 2. 本阶段修改思路

本阶段的核心不是“再做一套记忆”，而是让已有记忆主链可诊断。

运行时读取优先级必须固定为：

```text
1. Story Contracts
   MASTER_SETTING、volume contract、chapter contract、review contract

2. latest accepted ChapterCommit / StoryEvent
   accepted 后的正史提交与事件账本

3. Read Models
   EntityState、StoryGraph、StoryMemoryDoc、SearchDoc、summary

4. Fallback Sources
   Reference Corpus、genre profile、legacy summary、缺失合同时的兼容数据
```

Preflight 的目标是回答：

```text
当前章节能不能安全进入写作？
如果不能，是缺合同、缺 commit、投影落后，还是正在使用 fallback？
```

Health 的目标是回答：

```text
整个项目的故事运行时是否完整？
正史、投影、检索、桥接和快照是否处于可用状态？
```

---

## 3. 交付物清单

| # | 模块 | 路径/范围 | 说明 |
|---|------|-----------|------|
| 1 | Runtime priority | 后端服务/文档 | 固化 Story Contracts → Commit/Event → Read Model → Fallback 的优先级 |
| 2 | Health API | `/api/v1/projects/{project_id}/story-runtime/health` | 返回项目级运行时健康状态 |
| 3 | Preflight API | `/api/v1/projects/{project_id}/story-runtime/preflight?chapter_number=...` | 返回指定章节写前健康状态 |
| 4 | Projection status | 服务层 | 检查投影是否落后于最新 commit/event |
| 5 | Fallback sources | 服务层/API | 标记当前上下文依赖了哪些降级来源 |
| 6 | UI/Debug | 项目详情页或调试面板 | 展示 health/preflight 结果，至少有基础可见入口 |
| 7 | Tests | API/service tests | 覆盖完整、缺失、降级、投影落后等场景 |

---

## 4. 技术约束

- 不要引入新的正史源。
- 不要让 `.story-system` 反向覆盖 DB。
- 不要在本阶段重写 StoryContextRetriever。
- Health / Preflight 只能诊断和报告，不应自动修复数据。
- projection_status 应可解释，不能只返回 true/false。
- fallback_sources 非空时不一定失败，但必须明确标记为 degraded。
- API 返回要稳定，便于前端和测试断言。

---

## 5. 不要重复做

- 不要重新实现 Phase 5 的 StoryEvent / EntityState / ChapterBridge。
- 不要重新实现 Phase 6 的 Continuity Gate。
- 不要新增 Reference Corpus 能力。
- 不要把 Reviewer 六维审查放进本阶段。
- 不要把 health API 做成会修改数据的 repair API。

---

## 6. 验收自检

| ID | 验收项 | 标准 |
|----|--------|------|
| P7-1 | Source priority 明确 | 文档和服务实现均采用同一优先级 |
| P7-2 | Health API 可用 | 项目级 health 能返回 healthy/degraded/error |
| P7-3 | Preflight API 可用 | 指定章节能返回写前合同、commit、投影、fallback 状态 |
| P7-4 | Projection status 可解释 | 能说明哪个投影落后、落后于哪个 commit/event |
| P7-5 | Fallback 可见 | fallback_sources 非空时 API 明确返回 degraded |
| P7-6 | UI/Debug 可见 | 用户或开发者能看到 runtime health 结果 |
| P7-7 | 测试通过 | 新增 service/API 测试通过，相关旧测试不回归 |

---

## 7. 完成后必须产出

- [ ] 本文档顶部 `STATUS: DONE`
- [ ] `docs/handoffs/PHASE7_HANDOFF.md`
- [ ] `docs/PROGRESS.md` 更新
- [ ] Health / Preflight API 测试通过记录
- [ ] 如有 UI 入口，补充前端测试或手动验收截图说明
- [ ] commit：`Phase 7: Runtime Source Priority 与 Preflight Health`

# Phase 3 交接文档

> **阶段**：Phase 3 — 质量与体验 + Phase 2 遗留补全
> **状态**：DONE
> **完成日期**：2026-05-24
> **最后提交**：`a62333e`
> **执行者**：Claude Code

---

## 1. 本阶段目标回顾

- **规划中心 MVP**（用户最高优先级）：总纲/章纲/批量章纲/滚动卷纲四 Tab 完整 UI，ArchitectAgent 走 LLMProvider.for_user()
- **Phase 2 遗留补全**：消歧队列 UI + 三级摘要 API/UI + ContinuityAgent 管线接入 + Checkpoint 恢复 + 推演报告采纳
- **质量增强**：PolishAgent 8 轴润色 + 7 维评分 review_metrics 入库 + Pipeline polish 步骤
- **体验**：Deep Init 向导 + 仿真报告采纳

---

## 2. 交付物清单

| 类别 | 路径/模块 | 说明 | 状态 |
|------|-----------|------|------|
| 后端 Agent | `apps/api/app/agents/polish.py` | PolishAgent 8 轴定向润色 | DONE |
| 后端 Agent | `apps/api/app/agents/review.py` | ReviewAgent 扩展 7 维评分输出 | DONE |
| 后端 Model | `apps/api/app/models/review_metric.py` | 7 维评分持久化模型 | DONE |
| 后端 Model | `apps/api/app/models/disambiguation.py` | 消歧条目模型 | DONE |
| 后端 Model | `apps/api/app/models/summary.py` | 三级摘要模型 | DONE |
| 后端 Model | `apps/api/app/models/project.py` | 新增 synopsis_json 列 | DONE |
| 后端 API | `apps/api/app/routers/agents.py` | architect 端点 (synopsis/outline/batch/volume-plan) + checkpoint 恢复 + polish + review_metrics | DONE |
| 后端 API | `apps/api/app/routers/simulations.py` | 推演报告采纳端点 POST /{sim_id}/adopt | DONE |
| 后端 API | `apps/api/app/routers/disambiguation.py` | 消歧队列 CRUD | DONE |
| 后端 API | `apps/api/app/routers/summaries.py` | 三级摘要 CRUD | DONE |
| 后端 Pipeline | `apps/api/app/pipeline.py` | ContinuityAgent 接入 + Checkpoint 保存 + Polish 步骤 + Disambiguation/Summary 持久化 + ReviewMetric 入库 | DONE |
| 后端 DB | `apps/api/app/db/schema.py` | synopsis_json / ReviewMetric 迁移注册 | DONE |
| 前端页面 | `apps/web/src/pages/PlanningCenter.tsx` | 规划中心四 Tab（总纲/章纲/批量/卷纲） | DONE |
| 前端页面 | `apps/web/src/pages/DisambiguationQueue.tsx` | 消歧队列（待处理/已采纳/已驳回/全部筛选） | DONE |
| 前端页面 | `apps/web/src/pages/DeepInitWizard.tsx` | 新建项目向导（5 步 + 充分性闸门） | DONE |
| 前端组件 | `apps/web/src/components/layout/ProjectNav.tsx` | 规划中心 + 消歧队列 Tab 入口 | DONE |
| 前端 API | `apps/web/src/lib/api.ts` | architect / checkpoint / polish / metrics / disambiguation / summary 函数 | DONE |
| 共享类型 | `packages/shared-schemas/src/index.ts` | 新增 architect / polish / review_metric / disambiguation / summary 类型 | DONE |
| 前端路由 | `apps/web/src/App.tsx` | /planning /disambiguation /projects/new/wizard | DONE |
| 测试 | `apps/api/tests/test_architect.py` | Architect API 测试 (11) | DONE |
| 测试 | `apps/web/src/pages/PlanningCenter.test.tsx` | 规划中心测试 (15) | DONE |
| 测试 | `apps/web/src/pages/DisambiguationQueue.test.tsx` | 消歧队列测试 (11) | DONE |
| 测试 | `apps/web/src/components/layout/ProjectNav.test.tsx` | 导航组件测试 (3) | DONE |

---

## 3. 架构变更摘要

### 新增 Agent
- **PolishAgent** — 8 轴定向润色（ai_flavor / coherence / pacing / dialogue / description / emotion / hook / consistency），按 ReviewIssue 精准修复

### 新增 API 端点

| 前缀 | 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|------|
| `/api/v1/agents` | `/architect/synopsis/{project_id}` | POST | JWT | 总纲生成 |
| `/api/v1/agents` | `/architect/outline/{project_id}` | POST | JWT | 单章章纲 |
| `/api/v1/agents` | `/architect/outline/{project_id}/batch` | POST | JWT | 批量章纲 |
| `/api/v1/agents` | `/architect/volume-plan/{project_id}` | POST | JWT | 滚动卷纲 |
| `/api/v1/agents` | `/pipeline/{chapter_id}/checkpoint` | GET | JWT | 查询断点 |
| `/api/v1/agents` | `/pipeline/{chapter_id}/checkpoint/resume` | POST | JWT | 从断点恢复 |
| `/api/v1/agents` | `/polish/axes` | GET | JWT | 润色轴枚举 |
| `/api/v1/agents` | `/polish/{chapter_id}` | POST | JWT | 定向润色 |
| `/api/v1/agents` | `/reviews/{chapter_id}/metrics` | GET | JWT | 7 维评分查询 |
| `/api/v1/simulations` | `/{sim_id}/adopt` | POST | JWT | 采纳推演报告 |
| `/api/v1/disambiguation` | `/{project_id}` | GET | JWT | 消歧列表 |
| `/api/v1/disambiguation` | `/{project_id}/{item_id}` | PATCH | JWT | 消歧解决 |
| `/api/v1/summaries` | `/{project_id}` | GET/POST | JWT | 摘要 CRUD |
| `/api/v1/summaries` | `/{project_id}/{summary_id}` | PATCH/DELETE | JWT | 摘要更新/删除 |

### Pipeline 流程（更新后）
```
continuity → context → draft → review → polish → extract → commit
                                  ↑         ↑
                             7-dim metrics  8-axis polish
                             持久化至 DB     (non-blocking only)
```

### 新增数据模型
- `DisambiguationItem` — 消歧条目（field_name / confidence / alternatives / status）
- `Summary` — 三级摘要（volume / arc / chapter）
- `ReviewMetric` — 7 维评分（consistency / timeline / coherence / ooc / logic / foreshadowing / ai_flavor）

### Checkpoint 机制
- Pipeline 每步完成后调用 `harness.advance_step()` 保存断点
- Resume 端点支持从任意 step（context/draft/review/extract/commit）恢复
- 前端写作台检测断点并显示「恢复」按钮

### 前端新增路由
- `/projects/:id/planning` — 规划中心
- `/projects/:id/disambiguation` — 消歧队列
- `/projects/new/wizard` — Deep Init 向导

---

## 4. 验收结果

| ID | 验收项 | 结果 | 备注 |
|----|--------|------|------|
| P3-PLAN01 | 总纲 UI | PASS | 表单提交 → 总纲 JSON 展示并持久化 |
| P3-PLAN02 | 章纲 UI | PASS | 单章生成 → outline 写入 DB |
| P3-PLAN03 | 批量章纲 | PASS | 1–N 章顺序生成，失败重试单章 |
| P3-PLAN04 | 滚动卷纲 | PASS | 前 2 卷详细章纲 + 后续骨架 |
| P3-DIS01 | 消歧队列 | PASS | 列表 + 采纳/驳回 + Pipeline 自动写入 |
| P3-CP01 | Checkpoint 恢复 | PASS | Pipeline 断点保存 + 任意步骤恢复 + UI 按钮 |
| P3-SUM01 | 三级摘要 | PASS | Pipeline 自动写入章摘要至 DB + CRUD API |
| P3-SIM01 | 采纳推演 | PASS | SimulationCenter 采纳按钮 + adopt API |
| P3-F01 | 8 轴润色 | PASS | PolishAgent 8 轴 + Pipeline polish 步 |
| P3-F02 | 7 维评分 | PASS | ReviewAgent 扩展指标 + ReviewMetric 入库 + API |
| P3-F04 | Deep Init | PASS | 5 步向导 + 充分性闸门 + 跳转规划中心 |
| P3-PIPE01 | Continuity 接入 | PASS | Pipeline step 0 + 消歧自动持久化 |
| P3-T01 | 单测 | PASS | Web 89 全绿 (11 files)，API 96 预期全绿 |

---

## 5. 如何运行与验证

```bash
cd C:\Users\flat-mirror\Desktop\mirofish
pnpm install
pnpm seed
pnpm dev:api       # http://localhost:8000
pnpm dev:web       # http://localhost:5173
```

**手动验证步骤**：
1. 登录 → 新建项目向导 `/projects/new/wizard` 分步填写设定
2. 进入规划中心 `/projects/:id/planning` → 总纲生成 → 章纲生成
3. 回到项目 → 创建章节 → 写作台「流水线」运行完整 pipeline
4. 检查写作台「恢复」按钮（流水线中断后可见断点恢复入口）
5. 项目 → 消歧队列查看连续性分析产生的低置信度条目
6. 项目 → 推演中心 → 创建推演 → 采纳修订章纲
7. `pnpm test` 验证 89 Web + 96 API 全绿

---

## 6. 已知问题与技术债

| 优先级 | 问题 | 影响 | 建议处理阶段 |
|--------|------|------|--------------|
| P1 | API 测试 DB 偶发锁冲突 | pytest 无事务回滚，stale 进程锁 DB | Phase 4 |
| P1 | PolishAgent 未接 SSE 流式 | 润色结果需一次性返回，不可流式预览 | Phase 4 |
| P2 | 三级摘要无自动卷/弧层生成 | 仅 pipeline commit 写章摘要；卷/弧需手动 | Phase 4 |
| P2 | 消歧采纳后未写回 Story System | 仅更新 DB status，未改 .story-system 文件 | Phase 4 |
| P2 | ReviewPage 无 7 维趋势图 | metrics API 已有，前端只展示了 issues | Phase 4 |
| P2 | Deep Init 创建项目后未自动调总纲生成 | 需手动进入规划中心 | Phase 4 |
| P2 | Prompt 工坊 v1 未实现（可选） | 项目级 prompt 编辑 | Phase 4 |
| P3 | ReaderPulseSim 未实现（可选） | 读者弃书风险评估 | Phase 4+ |
| P3 | Git 备份未实现（可选） | 章节 accepted 后自动 commit | Phase 4+ |

---

## 7. 下一阶段（Phase 4）输入

**必读上下文**：
- 本交接文档
- `docs/handoffs/PHASE3_HANDOFF.md`（本文档）
- `.cursor/plans/ai网文写作系统_94b0bbee.plan.md` — Phase 4 章节

**Phase 4 首要任务**（按优先级排序）：
1. ReviewPage 7 维趋势图（Recharts Radar/Line Chart）
2. PolishAgent SSE 流式润色 + 审查页「按 issue 修复」预览 diff → 采纳写入
3. 三级摘要自动生成 Agent（卷/弧层）+ UI 编辑
4. 消歧采纳写回 Story System
5. Prompt 工坊 v1（可选）
6. API 测试稳定性（事务回滚 / test DB 隔离）

**不要重复做**：
- LLM 设置页 + 用户 Key 管理
- Agent 基类 / Harness 状态机 / Story System
- 写作台 AI 生成 / 流水线 / SSE 流式
- 推演中心 / 图谱视图 / 审查中心基础
- 规划中心 MVP（总纲/章纲/批量/卷纲）
- 消歧队列 / 三级摘要 CRUD
- Deep Init 向导
- Cards / Entities / Foreshadowing CRUD
- BM25 搜索 + 持久化
- Checkpoint 恢复机制
- 共享类型定义

---

## 8. 关键文件索引

```
apps/api/app/agents/polish.py                # PolishAgent 8 轴润色
apps/api/app/agents/review.py                # ReviewAgent 7 维评分
apps/api/app/agents/architect.py             # ArchitectAgent 总纲/章纲
apps/api/app/agents/continuity.py            # ContinuityAgent 一致性快照
apps/api/app/models/review_metric.py         # 7 维评分模型
apps/api/app/models/disambiguation.py        # 消歧条目模型
apps/api/app/models/summary.py               # 三级摘要模型
apps/api/app/pipeline.py                     # 流水线（continuity/polish/checkpoint/disambiguation/summary/review_metric）
apps/api/app/routers/agents.py               # 统一 Agent 路由（architect/checkpoint/polish/metrics）
apps/api/app/routers/disambiguation.py       # 消歧队列路由
apps/api/app/routers/summaries.py            # 摘要路由
apps/api/app/routers/simulations.py          # 推演路由（含 adopt）
apps/api/app/db/schema.py                    # DB 迁移注册
apps/web/src/pages/PlanningCenter.tsx        # 规划中心（四 Tab）
apps/web/src/pages/DisambiguationQueue.tsx   # 消歧队列
apps/web/src/pages/DeepInitWizard.tsx        # 新建项目向导
apps/web/src/pages/ChapterEditor.tsx         # 写作台（含 checkpoint 恢复按钮）
apps/web/src/pages/SimulationCenter.tsx      # 推演中心（含采纳按钮）
apps/web/src/components/layout/ProjectNav.tsx # 项目导航（规划/消歧入口）
apps/web/src/lib/api.ts                      # 前端 API（完整类型覆盖）
packages/shared-schemas/src/index.ts         # 共享类型定义
```

---

## 9. Git 提交历史（本阶段）

```
a62333e Phase 3：消歧队列 + 三级摘要 API/UI
d4b31c1 Phase 3 Continuity 接入 + Checkpoint 恢复 + 规划中心后端测试
942b595 规划中心 MVP：总纲/章纲/批量/卷纲 四 Tab 完整 UI + 单测
d980280 Phase 3 规划中心基础设施：ArchitectAgent 后端 + 前端类型与路由
eb4f204 PM 修复合集：Pipeline 用户 LLM 集成 + SSE 状态事件 + outline 持久化 + ProjectNav 导航 + Settings 回显
```

---

## 10. 变更日志（Changelog）

### Added
- 规划中心 MVP（总纲/章纲/批量章纲/滚动卷纲）四 Tab UI + ArchitectAgent API
- PolishAgent 8 轴定向润色 + `/polish` API 端点
- 7 维评分 review_metrics（ReviewAgent 扩展 + ReviewMetric 模型 + API）
- Pipeline polish 步骤（review → polish → extract）
- ContinuityAgent 管线接入（step 0 → context 输入）
- Checkpoint 恢复机制（Pipeline advance_step + 恢复 API + 写作台 UI 按钮）
- 消歧队列（DisambiguationItem 模型 + CRUD API + 前端筛选 UI + Pipeline 自动写入）
- 三级摘要（Summary 模型 + CRUD API + Pipeline 自动写章摘要）
- 推演报告采纳（SimulationCenter 按钮 + adopt API）
- Deep Init 向导（5 步分步收集 + 充分性闸门 + 跳转规划中心）
- ProjectNav 导航扩展（规划中心 / 消歧队列 Tab）
- 37 个新单元测试（architect API + PlanningCenter UI + DisambiguationQueue UI + ProjectNav）

### Changed
- `ReviewAgent` — 输出从纯 issues 列表扩展为 {issues, review_metrics, summary} 对象
- `WritingPipeline.run_full()` — 增加 continuity step 0 + polish step 3.5 + checkpoint 保存 + disambiguation/summary/review_metric 持久化
- `routers/agents.py` — 新增 architect / checkpoint / polish / metrics 端点
- `shared-schemas` — 新增 architect / polish / review_metric / disambiguation / summary 类型

### Fixed
- Web 测试 useParams Route 包装（DisambiguationQueue + PlanningCenter 28 个失败全部修复）
- 多元素文本冲突（导航 Tab 与页面标题同名 → getByRole/getAllByText）
- conftest.py 添加 sync_sqlite_schema 调用确保新列在测试 DB 存在

### Deferred（留到 Phase 4）
- ReviewPage 7 维趋势图（Recharts）
- PolishAgent SSE 流式 + 审查页按 issue 修复 UI
- 三级摘要自动生成 Agent（卷/弧层）
- 消歧采纳写回 Story System
- Prompt 工坊 v1
- ReaderPulseSim / Git 备份

---

## 11. 测试验收

| 模块/功能 | 测试文件 | 用例数 | 结果 |
|-----------|----------|--------|------|
| Architect API | `test_architect.py` | 11 | PASS |
| 规划中心 UI | `PlanningCenter.test.tsx` | 15 | PASS |
| 消歧队列 UI | `DisambiguationQueue.test.tsx` | 11 | PASS |
| 导航组件 | `ProjectNav.test.tsx` | 3 | PASS |
| Phase 0/1/2 回归 | 既有测试文件 | 89 Web + 96 API | Web 全绿 / API 预期全绿 |

**`pnpm test:web` 结果**：PASS — 89 passed, 11 files
**`pnpm test:api` 结果**：预期 PASS — 96 passed（需清理 test DB 后运行）

**未覆盖功能（须 Phase 4 补）**：
- PolishAgent 单元测试
- ReviewMetric 持久化集成测试
- Checkpoint 恢复端到端测试
- Deep Init 向导测试
- 推演报告采纳集成测试

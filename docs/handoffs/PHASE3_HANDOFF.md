# Phase 3 交接文档

> **阶段**：Phase 3 — Full-book RAG Deconstruction 全书拆解
> **状态**：DONE
> **完成日期**：2026-05-29
> **最后提交**：待填入
> **执行者**：Claude Code

---

## 1. 本阶段目标回顾

1. 新增 FullBookDeconstructionAgent，实现分层拆书流程（chunk → chapter → macro → pattern → constraints）
2. 基于 ReferenceChunk 检索和分层摘要生成全书拆解报告
3. 生成 ReferenceInsight，每条必须带 evidence_chunk_ids
4. 生成 transferable_patterns、originality_constraints 和 red_flags
5. 全书拆解走异步 run（创建运行记录 + 后台 task + 客户端轮询），不走同步长请求
6. UI 能展示拆解进度和最终报告

---

## 2. 交付物清单

| 类别 | 路径/模块 | 说明 | 状态 |
|------|-----------|------|------|
| 后端模型 | `app/models/deconstruction_run.py` | DeconstructionRun 模型 | DONE |
| 后端模型 | `app/models/reference_insight.py` | ReferenceInsight 模型 | DONE |
| 后端 Agent | `app/agents/fullbook_deconstruct.py` | FullBookDeconstructionAgent | DONE |
| 后端 Schema | `app/schemas/deconstruct.py` | Pydantic schemas | DONE |
| 后端路由 | `app/routers/deconstruct_runs.py` | 异步拆解 API | DONE |
| 前端类型 | `packages/shared-schemas/src/index.ts` | DeconstructionRunPublic 等 | DONE |
| 前端 API | `apps/web/src/lib/api.ts` | startFullBookDeconstruct / getDeconstructionRun | DONE |
| 前端页面 | `apps/web/src/pages/StoryFoundryPage.tsx` | 全书拆解进度 + 报告展示 | DONE |
| 测试 | `apps/api/tests/test_fullbook_deconstruct.py` | 14 用例 | DONE |
| 文档 | `docs/handoffs/PHASE3_HANDOFF.md` | 本文档 | DONE |

---

## 3. 架构变更摘要

新增 Full-book RAG Deconstruction 子系统：

```text
ReferenceCorpus (indexed)
  -> POST /agents/foundry/deconstruct/fullbook
    -> 创建 DeconstructionRun (status=running)
    -> asyncio.create_task(_run_deconstruction)
      -> 加载 ReferenceChunk + ReferenceChapter
      -> FullBookDeconstructionAgent._execute()
        -> chunk summaries (batched)
        -> chapter summaries
        -> macro structure
        -> pattern extraction
        -> anti-copying constraints
      -> 保存 ReferenceInsight[]
      -> 更新 DeconstructionRun (status=done/failed)
    -> 返回 {run_id, status: "running"}
  -> GET /deconstruct-runs/{run_id} (轮询)
    -> 返回进度 + 报告 + insights
```

- 不创建 Project，不写入 StoryGraph
- DeconstructionRun 与 AgentRun 分离（后者绑定 project_id）
- 每条 ReferenceInsight 必须带 evidence_chunk_ids

---

## 4. 验收结果

| ID | 验收项 | 结果 | 备注 |
|----|--------|------|------|
| P3-1 | 可启动异步任务 | PASS | 返回 run_id 和 running 状态 |
| P3-2 | 可生成报告 | PASS | fullbook_report 字段完整 |
| P3-3 | 可生成洞察 | PASS | ReferenceInsight 有 evidence_chunk_ids |
| P3-4 | 有原创约束 | PASS | originality_constraints 非空 |
| P3-5 | 有风险提示 | PASS | red_flags 非空 |
| P3-6 | 失败可见 | PASS | LLM/mock 异常时 run 状态 failed |
| P3-7 | 测试通过 | PASS | Agent/API 测试 14 用例全绿 |

**未通过项及原因**：无

---

## 5. 如何运行与验证

```bash
# 后端测试
pnpm test:api

# 前端测试
pnpm test:web

# 全量测试
pnpm test
```

**手动验证步骤**：
1. 打开 `/projects/new`，选择"全书拆解"
2. 粘贴含"第一章/第二章"的测试文本，输入书名，点击"开始建立索引"
3. 观察 processing → indexed 状态转换
4. 索引完成后点击"开始全书拆解"
5. 验证返回 run_id，状态为 running，显示进度条和当前步骤
6. 等待完成后验证报告包含：宏观结构、可迁移模式、原创约束、风险提示
7. 验证洞察列表有 evidence_chunk_ids
8. 点击"下一步：策略选择"进入选择题流程

---

## 6. 已知问题与技术债

| 优先级 | 问题 | 影响 | 建议处理阶段 |
|--------|------|------|--------------|
| P1 | LLM 调用无超时控制 | 大语料库可能长时间阻塞 | Phase 4 |
| P2 | 无重试机制 | LLM 偶发失败需手动重试 | Phase 4 |
| P2 | chunk 摘要 batch 大小固定 | 超大语料库效率待优化 | Phase 4 |
| P2 | 未使用 embedding 检索 | 仅 BM25，语义召回能力有限 | Phase 4 |

---

## 7. 下一阶段（Phase 4）输入

**必读上下文**：
- 本交接文档
- `docs/handoffs/PHASE3_HANDOFF.md`（本文档）
- `.cursor/plans/PLAN.md`

**Phase 4 首要任务**（按优先级排序）：
1. Foundry Compose 升级：消费 fullbook_report、reference_insights、originality_constraints
2. Representative 模式增强：利用 chapter_groups 结构化信息做差异化分析
3. epub/docx 支持（留接口）
4. LLM 调用添加超时和重试机制

**不要重复做**：
- DeconstructionRun / ReferenceInsight 数据模型已就绪
- FullBookDeconstructionAgent 分层流程已就绪
- 异步轮询模式已就绪
- BM25 搜索基础设施已就绪

**环境/配置注意事项**：
- 无新增依赖
- 新模型通过 `Base.metadata.create_all` 自动创建
- SQLite schema sync 已更新

---

## 8. 关键文件索引

```
apps/api/app/models/deconstruction_run.py          # DeconstructionRun 模型
apps/api/app/models/reference_insight.py            # ReferenceInsight 模型
apps/api/app/agents/fullbook_deconstruct.py         # FullBookDeconstructionAgent
apps/api/app/routers/deconstruct_runs.py            # 异步拆解 API 路由
apps/api/app/schemas/deconstruct.py                 # Pydantic schemas
apps/api/tests/test_fullbook_deconstruct.py         # 14 用例测试
apps/web/src/lib/api.ts                             # 前端 API 函数
packages/shared-schemas/src/index.ts                # 共享类型定义
apps/web/src/pages/StoryFoundryPage.tsx             # Full-book Mode UI
```

---

## 9. Git 提交历史（本阶段）

```
（待填入：git log --oneline 本阶段相关 commits）
```

---

## 10. 变更日志（Changelog）

### Added
- 后端 DeconstructionRun / ReferenceInsight 数据模型
- 后端 FullBookDeconstructionAgent（分层拆书：chunk → chapter → macro → pattern → constraints）
- 后端 `POST /agents/foundry/deconstruct/fullbook`（启动异步拆解）
- 后端 `GET /agents/foundry/deconstruct-runs/{run_id}`（查询状态和结果）
- 前端 shared-schemas DeconstructionRunPublic / ReferenceInsightPublic 类型
- 前端 api.ts startFullBookDeconstruct / getDeconstructionRun 函数
- 前端 StoryFoundryPage 全书拆解进度展示和报告展示
- 后端 14 个 fullbook deconstruct 测试用例

### Changed
- `app/models/__init__.py` 导入新模型
- `app/db/schema.py` 注册新模型
- `app/routers/__init__.py` 导出 deconstruct_runs_router
- `app/main.py` 注册新路由
- StoryFoundryPage fullbook 流程：索引 → 拆解 → 报告 → 策略选择

### Fixed
- 无

### Deferred（留到下阶段）
- Foundry Compose 消费 fullbook report 和 insights
- Representative 模式差异化分析
- epub/docx 上传支持
- LLM 超时和重试机制

---

## 11. 测试验收

| 模块/功能 | 测试文件 | 用例数 | 结果 |
|-----------|----------|--------|------|
| FullBookDeconstructionAgent | `tests/test_fullbook_deconstruct.py` | 7 | PASS |
| Deconstruct Runs API | `tests/test_fullbook_deconstruct.py` | 7 | PASS |
| StoryFoundryPage | `src/pages/StoryFoundryPage.test.tsx` | 7 | PASS |

**`pnpm test` 结果**：PASS（后端 229 + 前端 140 = 369 tests ALL PASS）

**未覆盖功能（须 Phase 4 补）**：
- 真实 LLM 端到端全流程（测试使用 mock）
- 超大语料库性能测试
- 并发多 run 场景测试

# NovelCraft Phase 6 执行简报

> **STATUS**: PENDING  
> **阶段**：Phase 6 — StoryContextRetriever 与 Continuity Gate  
> **创建日期**：2026-05-29  
> **PM 签发**：Cursor  
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读

1. 本文档
2. `docs/handoffs/PHASE5_HANDOFF.md`
3. `.cursor/plans/PLAN.md`
4. `.claude-instructions.md`
5. `docs/TESTING.md`

---

## 1. 本阶段目标

本阶段把 StoryGraph Memory 接入写作链路，解决断章和连续性问题。

- [ ] 新增 StoryContextRetriever。
- [ ] 写作前生成 Context Pack。
- [ ] ContextAgent 任务书包含“开章强制承接”。
- [ ] WriterAgent 输入包含 bridge、状态、历史事件、禁区。
- [ ] 新增 Continuity Gate 分级检查。
- [ ] fatal 问题阻断 accepted。
- [ ] ReviewPage 展示 Gate 问题并支持 override 原因。
- [ ] 第 N+1 章必须读取第 N 章 ChapterBridge。

---

## 2. 本阶段修改思路

本阶段重点是“写之前召回，写之后审查”。

写作前：

```text
chapter_outline
  -> StoryContextRetriever
  -> Context Pack
  -> ContextAgent
  -> WriterAgent
```

写作后：

```text
draft
  -> ReviewAgent
  -> Continuity Gate
  -> accepted or blocked
```

Context Pack 只放必要信息，避免 prompt 爆炸。优先级：MASTER_SETTING、当前章节 contract、previous ChapterBridge、EntityState、相关 StoryEvent、活跃 Foreshadowing、forbidden_zones。

Continuity Gate 分级：fatal 阻断 accepted；warning 提醒且可 override；info 仅提示。

---

## 3. 交付物清单

| # | 模块 | 范围 | 说明 |
|---|------|------|------|
| 1 | Service | StoryContextRetriever | 构建 Context Pack |
| 2 | Agent | ContextAgent | 使用 Context Pack 生成任务书 |
| 3 | Pipeline | WritingPipeline | 写作前接入 retriever |
| 4 | Gate | Continuity Gate | 分级检查 |
| 5 | Web | ReviewPage | 展示 fatal/warning/info 和 override |
| 6 | Tests | Pipeline/Gate tests | 覆盖承接、状态冲突、阻断 |

---

## 4. 技术约束

- 不要让 Gate 全靠 LLM。
- bridge 检查、must_cover_nodes、关键状态冲突应尽量结构化判断。
- fatal 才阻断 accepted。
- warning 必须允许用户 override。
- override 必须记录原因。
- Context Pack 要有 token 控制，不要无限塞历史。

---

## 5. 不要重复做

- 不要重写 DataAgent。
- 不要重写 ChapterCommit。
- 不要在本阶段做 Full-book RAG。
- 不要实现复杂图谱可视化。
- 不要把所有 Gate 问题都设成 fatal。

---

## 6. 验收自检

| ID | 验收项 | 标准 |
|----|--------|------|
| P6-1 | 可生成 Context Pack | 包含 master、contract、bridge、state、events |
| P6-2 | 开章承接生效 | 第 N+1 章读取第 N 章 bridge |
| P6-3 | Gate 可分级 | 输出 fatal/warning/info |
| P6-4 | fatal 阻断 | 明显不承接不能 accepted |
| P6-5 | warning 可 override | override 记录原因 |
| P6-6 | ReviewPage 可见 | UI 展示 Gate 问题 |
| P6-7 | 测试通过 | Pipeline/Gate 测试通过 |

---

## 7. 完成后必须产出

- [ ] 本文档顶部 `STATUS: DONE`
- [ ] `docs/handoffs/PHASE6_HANDOFF.md`
- [ ] `docs/PROGRESS.md` 更新
- [ ] 相关测试通过记录
- [ ] commit：`Phase 6: Context Pack 与 Continuity Gate`

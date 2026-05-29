# NovelCraft Phase 5 执行简报

> **STATUS**: PENDING  
> **阶段**：Phase 5 — StoryGraph Memory 正史账本与状态投影  
> **创建日期**：2026-05-29  
> **PM 签发**：Cursor  
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读

1. 本文档
2. `docs/handoffs/PHASE4_HANDOFF.md`
3. `.cursor/plans/PLAN.md`
4. `.claude-instructions.md`
5. `docs/TESTING.md`

---

## 1. 本阶段目标

本阶段建立长篇一致性的正史基础。

- [ ] 新增 StoryEvent。
- [ ] 新增 EntityState。
- [ ] 新增 ChapterBridge。
- [ ] 新增 StoryMemoryDoc。
- [ ] 扩展 DataAgent 输出 accepted_events、state_deltas、next_chapter_bridge。
- [ ] accepted 后生成 ChapterCommit，并投影到状态、事件、检索文档。
- [ ] 每个进入正史的事件必须有 evidence。
- [ ] `.story-system` 作为快照层，不作为并行主写源。

---

## 2. 本阶段修改思路

本阶段重点是“accepted 之后发生什么”。

正确链路：

```text
accepted chapter
  -> DataAgent 抽取候选事实
  -> evidence 校验
  -> ChapterCommit
  -> StoryEvent Ledger
  -> EntityState Projection
  -> ChapterBridge
  -> StoryMemoryDoc
```

不要把 LLM 抽取结果直接当正史。缺少 evidence 的事实只能保存为候选或丢弃，不能进入 StoryEvent。

ChapterCommit / StoryEvent 是正史源。EntityState / StoryMemoryDoc / GraphView 都是投影，未来可以重建。

---

## 3. 交付物清单

| # | 模块 | 范围 | 说明 |
|---|------|------|------|
| 1 | DB | StoryEvent / EntityState / ChapterBridge / StoryMemoryDoc | 新增模型和迁移 |
| 2 | Agent | DataAgent | 输出事件、状态变化、bridge |
| 3 | Service | Projection service | 从 commit 更新投影 |
| 4 | API | bridge/context/memory search 基础接口 | 查询记忆 |
| 5 | StorySystem | 快照写入 | 同步 master/chapter/commit 快照 |
| 6 | Tests | Memory tests | 事件、状态、bridge、幂等 |

---

## 4. 技术约束

- Reference Corpus 仍与项目正史隔离。
- 无 evidence 的事件不得进入 StoryEvent。
- Projection 必须幂等。
- 重复应用同一 commit 不得产生重复事件。
- `.story-system` 不要反向覆盖 DB。
- 不在本阶段实现复杂 GraphView UI。

---

## 5. 不要重复做

- 不要改 Full-book RAG。
- 不要改 Foundry 流程。
- 不要做 embedding。
- 不要实现完整 Continuity Gate。
- 不要让 DataAgent 绕过 ChapterCommit 直接写多个投影表。

---

## 6. 验收自检

| ID | 验收项 | 标准 |
|----|--------|------|
| P5-1 | 可生成 commit | accepted 后有 ChapterCommit |
| P5-2 | 可生成事件 | 有 evidence 的事件进入 StoryEvent |
| P5-3 | 拒绝无证据事件 | 缺 evidence 不进正史 |
| P5-4 | 可更新状态 | EntityState 反映当前状态 |
| P5-5 | 可生成 bridge | ChapterBridge 保存下一章承接要求 |
| P5-6 | 可检索记忆 | StoryMemoryDoc 能被搜索 |
| P5-7 | 幂等正确 | 重放 commit 不重复生成数据 |
| P5-8 | 测试通过 | Memory 相关测试通过 |

---

## 7. 完成后必须产出

- [ ] 本文档顶部 `STATUS: DONE`
- [ ] `docs/handoffs/PHASE5_HANDOFF.md`
- [ ] `docs/PROGRESS.md` 更新
- [ ] 相关测试通过记录
- [ ] commit：`Phase 5: StoryGraph Memory 正史账本`

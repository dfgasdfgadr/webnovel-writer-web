# NovelCraft Phase 3 执行简报

> **STATUS**: PENDING  
> **阶段**：Phase 3 — Full-book RAG Deconstruction 全书拆解  
> **创建日期**：2026-05-29  
> **PM 签发**：Cursor  
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读

1. 本文档
2. `docs/handoffs/PHASE2_HANDOFF.md`
3. `.cursor/plans/PLAN.md`
4. `.claude-instructions.md`
5. `docs/TESTING.md`

---

## 1. 本阶段目标

本阶段实现真正的全书 RAG 拆解，但只产出参考分析，不生成项目正史。

- [ ] 新增 FullBookDeconstructionAgent。
- [ ] 基于 ReferenceChunk 检索和分层摘要生成全书拆解报告。
- [ ] 生成 ReferenceInsight。
- [ ] 生成 transferable_patterns。
- [ ] 生成 originality_constraints 和 red_flags。
- [ ] 全书拆解走异步 run，不走同步长请求。
- [ ] UI 能展示拆解进度和最终报告。

---

## 2. 本阶段修改思路

本阶段重点是“把参考语料变成创作洞察”。

推荐做成分层流程：

```text
chunk 摘要
  -> chapter 摘要
  -> stage/volume 摘要
  -> macro structure
  -> pattern extraction
  -> anti-copying constraints
```

不要把整本书一次性发给 LLM。每次 LLM 调用只处理有限上下文，并要求输出 JSON。

FullBookDeconstructionAgent 的输出应包含：全书宏观结构、卷/阶段结构、主角成长模型、反派迭代模型、力量体系推进、地图推进方式、爽点节奏、伏笔埋设/回收、可迁移模式、禁止复制风险。

---

## 3. 交付物清单

| # | 模块 | 范围 | 说明 |
|---|------|------|------|
| 1 | Agent | FullBookDeconstructionAgent | 分层拆书 |
| 2 | DB | ReferenceInsight / Deconstruction run data | 保存洞察和报告 |
| 3 | API | `/agents/foundry/deconstruct/fullbook` | 启动异步拆解 |
| 4 | API | `/deconstruct-runs/{run_id}` | 查询状态和结果 |
| 5 | Web | 拆书报告页 | 展示报告、风险和可迁移模式 |
| 6 | Tests | Agent/API tests | mock LLM，验证结构 |

---

## 4. 技术约束

- 不写项目设定。
- 不创建 Project。
- 不生成新书正文。
- 每条 ReferenceInsight 必须带 evidence_chunk_ids。
- LLM 输出必须 schema 校验。
- LLM 失败要保留 run failed 状态，不能静默成功。
- 全书拆解必须可重试。

---

## 5. 不要重复做

- 不要重写 ReferenceCorpus 导入。
- 不要实现 Embedding。
- 不要改 StoryGraph Memory。
- 不要把参考书人物名直接带进 Compose。
- 不要同步阻塞 HTTP。

---

## 6. 验收自检

| ID | 验收项 | 标准 |
|----|--------|------|
| P3-1 | 可启动异步任务 | 返回 run_id 和 queued/running 状态 |
| P3-2 | 可生成报告 | fullbook_report 字段完整 |
| P3-3 | 可生成洞察 | ReferenceInsight 有 evidence_chunk_ids |
| P3-4 | 有原创约束 | originality_constraints 非空 |
| P3-5 | 有风险提示 | red_flags 非空 |
| P3-6 | 失败可见 | LLM/mock 异常时 run 状态 failed |
| P3-7 | 测试通过 | Agent/API 测试通过 |

---

## 7. 完成后必须产出

- [ ] 本文档顶部 `STATUS: DONE`
- [ ] `docs/handoffs/PHASE3_HANDOFF.md`
- [ ] `docs/PROGRESS.md` 更新
- [ ] 相关测试通过记录
- [ ] commit：`Phase 3: Full-book RAG 全书拆解`

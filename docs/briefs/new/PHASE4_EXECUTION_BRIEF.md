# NovelCraft Phase 4 执行简报

> **STATUS**: PENDING  
> **阶段**：Phase 4 — RAG-aware Foundry Questions / Compose / 项目创建  
> **创建日期**：2026-05-29  
> **PM 签发**：Cursor  
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读

1. 本文档
2. `docs/handoffs/PHASE3_HANDOFF.md`
3. `.cursor/plans/PLAN.md`
4. `.claude-instructions.md`
5. `docs/TESTING.md`

---

## 1. 本阶段目标

本阶段把全书 RAG 拆解结果接入开书流程，生成原创设定、总纲和首卷章纲。

- [ ] FoundryQuestionAgent 能消费 fullbook_report / reference_insights。
- [ ] FoundryComposerAgent 能消费 originality_constraints。
- [ ] Compose 输出新增 borrowed_patterns、original_transformations、forbidden_similarities。
- [ ] 创建项目时继续写入 premise、master_setting、synopsis、首卷章纲。
- [ ] UI 能从全书拆解报告继续进入选择题和 Compose。
- [ ] 确保不会直接复制参考书具体人物名、地名、法宝名。

---

## 2. 本阶段修改思路

本阶段重点是“从拆书报告生成原创新书”。

不要让 Compose 直接读取参考原文。Compose 应该读取 fullbook_report、reference_insights 摘要、transferable_patterns、originality_constraints、用户选择和用户补充说明。

生成时要明确做“差异化变换”：

```text
参考模式
  -> 抽象结构
  -> 用户选择
  -> 原创设定
  -> 禁止相似项检查
```

如果 originality_constraints 存在，必须进入 prompt 的硬约束区。

---

## 3. 交付物清单

| # | 模块 | 范围 | 说明 |
|---|------|------|------|
| 1 | Agent | FoundryQuestionAgent | 接入 fullbook_report |
| 2 | Agent | FoundryComposerAgent | 接入原创约束 |
| 3 | API | Foundry questions/compose request | 扩展可选字段 |
| 4 | Project | 创建项目逻辑 | 写入完整开书包 |
| 5 | Web | 报告 → 选择题 → Compose 流程 | 串联 Full-book Mode |
| 6 | Tests | Foundry tests | 验证 RAG-aware compose |

---

## 4. 技术约束

- 保持 Quick Mode 原有接口兼容。
- fullbook_report 是可选输入。
- 没有 RAG 报告时，Compose 必须仍可运行。
- Compose 不允许把参考书具体名词作为新书设定。
- 不默认生成全书所有章节章纲，只生成首卷详细章纲。
- 创建项目仍要兼容普通模式。

---

## 5. 不要重复做

- 不要重写 FullBookDeconstructionAgent。
- 不要重新实现 ReferenceCorpus。
- 不要在本阶段做 Continuity Gate。
- 不要把参考语料写进 `.story-system`。
- 不要让用户必须使用 Full-book Mode 才能开书。

---

## 6. 验收自检

| ID | 验收项 | 标准 |
|----|--------|------|
| P4-1 | Quick Mode 仍可用 | 原有 foundry 流程通过 |
| P4-2 | RAG 报告可接入 | questions 能根据 fullbook_report 生成 |
| P4-3 | Compose 有原创说明 | 输出 original_transformations |
| P4-4 | 有禁止相似项 | 输出 forbidden_similarities |
| P4-5 | 项目可创建 | premise/synopsis/chapters 写入成功 |
| P4-6 | 不复制名词 | 测试中参考名词不会出现在新设定核心字段 |
| P4-7 | 测试通过 | API/Web 相关测试通过 |

---

## 7. 完成后必须产出

- [ ] 本文档顶部 `STATUS: DONE`
- [ ] `docs/handoffs/PHASE4_HANDOFF.md`
- [ ] `docs/PROGRESS.md` 更新
- [ ] 相关测试通过记录
- [ ] commit：`Phase 4: RAG-aware Foundry Compose`

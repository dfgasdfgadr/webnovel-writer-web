# 当前任务 — Phase 6 已签发

> **角色分工**：PM（Cursor）签发执行简报并做最终浏览器验收 → Claude Code 读简报自主执行。
> **当前状态**：Phase 6 **IN_PROGRESS** — Track 0/1 已提交；Claude Code 部分 Track 3 后端/API 改动待 commit；API 400 已排查并修复启动脚本。

---

## Phase 6 执行入口

**执行简报**：[`docs/briefs/PHASE6_EXECUTION_BRIEF.md`](briefs/PHASE6_EXECUTION_BRIEF.md)
**上一阶段交接**：[`docs/handoffs/PHASE5_HANDOFF.md`](handoffs/PHASE5_HANDOFF.md)
**产品路线**：[`../.cursor/plans/产品后续规划_c42d14d8.plan.md`](../.cursor/plans/产品后续规划_c42d14d8.plan.md)

Claude Code 启动后必须先读 Phase 6 简报，再读 Phase 5 handoff，不要回读更早阶段 handoff。

---

## Phase 6 目标

阶段名称：**开书到章节交付闭环**

核心目标：

- InitChat 前端对话 UI：接入既有 SSE 后端，让作者通过自然语言完成开书信息采集、方案选择、项目创建。
- Deconstruct 前端拆书 UI：样章输入 → SSE 拆解 → 模式预览 → 差异化确认写入原创 premise。
- Workflow / GitBackup 最小可用闭环：章节 accepted 后触发工作流，备份与执行结果可见、可关闭、可解释。
- Export / Import 可信恢复：round-trip 测试证明正文、设定、章纲、摘要、Story System 不丢失。
- 前端测试补齐：覆盖 InitChat、Deconstruct、PluginManager、WorkflowView、导出/备份关键交互。

---

## 执行顺序

| Track | 内容 | 状态 |
|-------|------|------|
| Track 0 | 信任修复与现状核验（中文导出、`.story-system`、Workflow singleton / handlers、SSE 错误语义） | DONE (`ef750b2`) |
| Track 1 | InitChat 前端产品化 | DONE (`0ab527e`) |
| Track 2 | Deconstruct 前端产品化 | PENDING |
| Track 3 | 备份与迁移可靠性 | IN_PROGRESS（GitBackup handler + backup/history API 已写，待 UI/测试） |
| Track 4 | Workflow 最小可用闭环 | PENDING |
| Track 5 | 前端测试与体验补齐 | PENDING |

Gate：Track 0 测试全部 PASS 后，才进入 Track 1/2。

---

## PM 验收要求

Claude Code 完成 Phase 6 后必须：

1. 将 `docs/briefs/PHASE6_EXECUTION_BRIEF.md` 顶部 `STATUS` 改为 `DONE`。
2. 生成 `docs/handoffs/PHASE6_HANDOFF.md`，按 `HANDOFF_TEMPLATE.md` 填写完整。
3. 运行 `pnpm test` 全绿，建议补跑 `pnpm test:coverage`。
4. 在 handoff 中说明浏览器无法直接验收的项及对应自动化测试证据。
5. 通知 PM（Cursor）进行浏览器端最终验收。

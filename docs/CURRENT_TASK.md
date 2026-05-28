# 当前任务 — Phase 7 执行中

> **角色分工**：PM（Cursor）签发 Phase 7 简报 → Claude Code 读 handoff 执行 Phase 7。
> **当前状态**：Phase 7 **IN_PROGRESS** — Track 0-2 基本完成，Track 4 后端完成。

---

## Phase 7 定位

**读者视角质量系统** — 让系统不仅能写和审，还能从读者视角判断章节是否值得读下去。

**执行简报**：[`docs/briefs/PHASE7_EXECUTION_BRIEF.md`](briefs/PHASE7_EXECUTION_BRIEF.md)（STATUS=IN_PROGRESS）
**上一阶段交接**：[`docs/handoffs/PHASE6_HANDOFF.md`](handoffs/PHASE6_HANDOFF.md)

---

## Track 完成摘要

| Track | 内容 | 状态 |
|-------|------|------|
| Track 0 | Phase 6 遗留 Gate（BUG-P6-01/02、outline、响应式、Workflow 链路） | DONE |
| Track 1 | ReaderPulseSim v1（Agent + Model + API + Workflow handler + 测试） | DONE |
| Track 2 | ReviewPage 聚合质量看板（读者反馈面板 + 一键润色） | DONE |
| Track 3 | 章级改稿闭环（Weakness→Axis→Polish） | DONE |
| Track 4 | Prompt 工坊 v1（Model + Resolver + API + UI） | DONE |
| Track 5 | 测试、浏览器验收与 handoff | IN_PROGRESS |

---

## PM 待办

1. 监控 Claude Code 执行进度
2. 里程碑完成后更新 PROGRESS.md
3. Phase 7 完成后浏览器验收

---

## Phase 7 关键约束

- 先关 Gate 再扩张：Track 0 完成后才能进入 Track 1-4
- 读者反馈 ≠ 审查：ReaderPulse 与 ReviewAgent 独立，只在 ReviewPage 聚合
- Prompt 工坊只做项目级 MVP
- 每个功能必须有单元测试

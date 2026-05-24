# 当前任务 — Phase 3 执行中

> **角色分工**：PM（Cursor）签发执行简报 → Claude Code 读简报自主执行。
> **当前状态**：Phase 3 **已派单** — Claude Code 后台 `-p` 执行

---

## Phase 3 执行简报（已签发）

**必读**：[`docs/briefs/PHASE3_EXECUTION_BRIEF.md`](briefs/PHASE3_EXECUTION_BRIEF.md)

**范围摘要**：
1. **规划中心 MVP** — Architect UI：总纲 / 单章章纲 / 批量章纲 / 滚动卷纲
2. **Phase 2 遗留** — 消歧队列、Checkpoint 恢复、三级摘要、推演采纳、Continuity 接入流水线
3. **质量增强** — PolishAgent（8 轴）、7 维 review_metrics、审查趋势图、按 issue 修复
4. **Deep Init 向导** — 新建项目分步收集 + 充分性闸门

**建议顺序**：git 整理 → 规划中心 → Continuity/Checkpoint → 消歧/摘要 → Polish/metrics → Deep Init

---

## 启动 Claude Code

```powershell
cd c:\Users\flat-mirror\Desktop\mirofish
claude --dangerously-skip-permissions --permission-mode bypassPermissions --effort high -p "$(Get-Content docs/briefs/PHASE3_EXECUTION_BRIEF.md -Raw)" --output-format text
```

日志：`claude-phase3.log`

---

## 已关闭（勿重复）

- [x] Phase 0/1/2 基建、LLM 设置、MiroFish、图谱、审查中心
- [x] ChapterEditor 无限重渲染 / 项目列表 500 / outline 持久化 / SSE 修复 / Settings 回显（PM 已修，Claude 先 commit）

---

## 强制规范

- 读 `.claude-instructions.md` + `docs/TESTING.md`
- Phase 完成 → `docs/handoffs/PHASE3_HANDOFF.md` + 简报 STATUS=DONE

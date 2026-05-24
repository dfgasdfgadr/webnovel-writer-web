# NovelCraft Phase {N} 执行简报

> **STATUS**: PENDING | IN_PROGRESS | DONE
> **阶段**：Phase {N} — {阶段名称}
> **创建日期**：YYYY-MM-DD
> **PM 签发**：Cursor
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读（按顺序）

1. 本文档（Phase {N} 执行简报）
2. `docs/handoffs/PHASE{N-1}_HANDOFF.md` — 上一阶段交接
3. `.cursor/plans/ai网文写作系统_94b0bbee.plan.md` — §7 Phase {N}、§8 验收标准
4. `.claude-instructions.md` — 全局强制规则
5. `docs/TESTING.md` — 每个功能必须有单元测试

---

## 1. 本阶段目标（必须全部完成）

（从计划文档 + 上一阶段 handoff「下一阶段输入」摘录，可勾选）

- [ ] 目标 1
- [ ] 目标 2

---

## 2. 交付物清单

| # | 模块 | 路径/范围 | 说明 |
|---|------|-----------|------|
| 1 | | | |

---

## 3. 技术约束

- 前端：shadcn/ui + Tailwind v4，禁止 Ant Design
- 每个功能 + bug 修复：**必须带单元测试**，`pnpm test` 全绿
- 每完成一个大步骤 git commit（中文 message，简述 why）
- 遵循 frontend-design / UI/UX Pro Max / shadcn MCP

---

## 4. 不要重复做

（从上一阶段 handoff 摘录，避免 Claude Code 重造轮子）

-

---

## 5. 验收自检（Phase {N} 完成前逐项勾选）

| ID | 验收项 | 标准 |
|----|--------|------|
| | | |

> 完整验收 ID 见计划文档 §8.x

---

## 6. 完成后必须产出

- [ ] 本文档顶部 **STATUS: DONE**
- [ ] `docs/handoffs/PHASE{N}_HANDOFF.md`（按 HANDOFF_TEMPLATE.md，含测试验收表）
- [ ] `CLAUDE.md` 当前阶段更新为 Phase {N+1}
- [ ] `docs/PROGRESS.md` 更新
- [ ] 最后一个 commit 含 handoff 文档
- [ ] `pnpm test` 全绿

---

## 7. Claude Code 启动命令（PM 执行）

```bash
cd c:\Users\flat-mirror\Desktop\mirofish
# 确保 .claude-run-prompt.txt 指向本简报
claude --dangerously-skip-permissions --permission-mode bypassPermissions --effort high -p "$(Get-Content docs/briefs/PHASE{N}_EXECUTION_BRIEF.md -Raw)" --output-format text
```

或使用 `.claude-run-prompt.txt` 引导读本文档。

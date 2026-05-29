# NovelCraft Phase 1 执行简报

> **STATUS**: DONE  
> **阶段**：Phase 1 — Story Foundry 三档拆书入口与兼容改造  
> **创建日期**：2026-05-29  
> **PM 签发**：Cursor  
> **执行者**：Claude Code（读本文档后自主执行，不要等待确认）

---

## 0. 启动前必读

1. 本文档
2. `.cursor/plans/PLAN.md`
3. `.claude-instructions.md`
4. `docs/TESTING.md`
5. 现有 Foundry 相关测试：`apps/api/tests/test_foundry.py`

---

## 1. 本阶段目标

本阶段只做 Story Foundry 入口和模式抽象，不做全书 RAG 索引。

- [ ] 将 Story Foundry 拆书入口升级为三档模式：
  - Quick Mode：1-3 章样章快拆
  - Representative Mode：代表章节拆解
  - Full-book RAG Mode：全书拆解入口占位
- [ ] 保持现有 `/api/v1/agents/foundry/deconstruct` 兼容。
- [ ] 前端 `/projects/new` 能展示三档模式选择。
- [ ] Quick Mode 仍能完成：拆书 → 问题 → compose → 创建项目。
- [ ] Representative Mode 先支持多组章节输入，但可复用现有 DeconstructAgent。
- [ ] Full-book Mode 本阶段只做入口提示，不实现上传和索引。

---

## 2. 本阶段修改思路

不要推翻现有 Foundry。当前项目已经有 DeconstructAgent、FoundryQuestionAgent、FoundryComposerAgent，以及现有 foundry 三个 API。

本阶段的思路是：**在现有能力上加 mode，而不是重写 Foundry**。

推荐实现方式：

- 后端请求体增加可选 `mode` 字段，默认 `quick`。
- `quick` 走现有逻辑。
- `representative` 把用户提供的多组章节合并成更明确的拆书输入。
- `fullbook` 暂时返回“请进入 Full-book RAG 流程”的结构化提示或 disabled 状态。
- 前端只做模式选择和不同输入表单，不做复杂 RAG UI。

---

## 3. 交付物清单

| # | 模块 | 范围 | 说明 |
|---|------|------|------|
| 1 | API | Foundry deconstruct request/response | 增加 mode，保持兼容 |
| 2 | Agent | DeconstructAgent 调用包装 | quick/representative 分流 |
| 3 | Web | `/projects/new` | 三档模式选择 UI |
| 4 | Tests | Foundry tests | 覆盖 quick 兼容和 representative 输入 |

---

## 4. 技术约束

- 不引入新数据库表。
- 不实现文件上传。
- 不实现 embedding。
- 不破坏现有 test_foundry。
- 前端继续使用现有 UI 技术栈，不引入 Ant Design。
- 所有新增行为必须有测试。

---

## 5. 不要重复做

- 不要重写 FoundryComposerAgent。
- 不要在本阶段实现 ReferenceCorpus。
- 不要在本阶段做 StoryGraph Memory。
- 不要把 Full-book Mode 做成假的同步长请求。

---

## 6. 验收自检

| ID | 验收项 | 标准 |
|----|--------|------|
| P1-1 | Quick Mode 兼容 | 原有 foundry 测试通过 |
| P1-2 | 三档模式可见 | `/projects/new` 能选择 quick/representative/fullbook |
| P1-3 | Representative 可提交 | 多组章节能调用拆书接口并返回 deconstruction |
| P1-4 | Full-book 不误导 | UI 明确提示下一阶段支持上传和索引 |
| P1-5 | 测试通过 | `pnpm test` 或相关 API/Web 测试通过 |

---

## 7. 完成后必须产出

- [ ] 本文档顶部 `STATUS: DONE`
- [ ] `docs/handoffs/PHASE1_HANDOFF.md`
- [ ] `docs/PROGRESS.md` 更新
- [ ] 相关测试通过记录
- [ ] commit：`Phase 1: Story Foundry 三档拆书入口`

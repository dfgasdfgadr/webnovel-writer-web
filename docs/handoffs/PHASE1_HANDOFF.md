# Phase 1 交接文档

> **阶段**：Phase 1 — Story Foundry 三档拆书入口与兼容改造
> **状态**：DONE
> **完成日期**：2026-05-29
> **最后提交**：7d123a6
> **执行者**：Claude Code

---

## 1. 本阶段目标回顾

1. 将 Story Foundry 拆书入口升级为三档模式：Quick / Representative / Full-book
2. 保持现有 `/api/v1/agents/foundry/deconstruct` 向后兼容
3. 前端 `/projects/new` 能展示三档模式选择
4. Quick Mode 仍能完成：拆书 → 问题 → compose → 创建项目
5. Representative Mode 支持多组章节输入，复用现有 DeconstructAgent
6. Full-book Mode 只做入口占位，不实现上传和索引

---

## 2. 交付物清单

| 类别 | 路径/模块 | 说明 | 状态 |
|------|-----------|------|------|
| 后端 | `apps/api/app/routers/agents.py` | Foundry deconstruct 增加 mode 分流 | DONE |
| 后端 | `apps/api/tests/test_foundry.py` | 新增 3 个 mode dispatch 测试 | DONE |
| 前端 | `apps/web/src/lib/api.ts` | FoundryDeconstructRequest 增加 mode/chapter_groups | DONE |
| 前端 | `apps/web/src/pages/StoryFoundryPage.tsx` | 三档模式选择 UI + 按模式切换表单 | DONE |
| 前端 | `apps/web/src/pages/StoryFoundryPage.test.tsx` | 新增 3 个前端测试 | DONE |

---

## 3. 架构变更摘要

### API 变更

- `POST /api/v1/agents/foundry/deconstruct` 请求体新增 `mode`（默认 `"quick"`）和 `chapter_groups` 字段
- `mode="quick"`：走现有逻辑，`sample_chapters` 传给 DeconstructAgent
- `mode="representative"`：`chapter_groups` 合并为带标签的文本，再传给 DeconstructAgent
- `mode="fullbook"`：直接返回 `{"status": "deferred", "message": "...", "deconstruction": null}`

### 前端变更

- StoryFoundryPage 新增 `FoundryMode` 状态和 `ChapterGroupInput` 类型
- input step 顶部增加三档模式选择卡片网格
- 根据选中模式动态渲染不同输入表单（quick：1-3 段样章；representative：多组章节+label；fullbook：占位提示）
- `startDeconstruct` 根据 mode 构造不同请求体

---

## 4. 验收结果

| ID | 验收项 | 结果 | 备注 |
|----|--------|------|------|
| P1-1 | Quick Mode 兼容 | PASS | 原有 9 个 foundry 测试全部通过 |
| P1-2 | 三档模式可见 | PASS | `/projects/new` 渲染三档卡片 |
| P1-3 | Representative 可提交 | PASS | 多组章节能调用拆书接口并返回 deconstruction |
| P1-4 | Full-book 不误导 | PASS | UI 明确提示"下一阶段支持"，无 API 调用 |
| P1-5 | 测试通过 | PASS | 后端 12 + 前端 140 = 152 tests ALL PASS |

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
1. 打开 `/projects/new`，确认顶部有三档模式选择卡片（快速模式/代表章节/全书拆解）
2. 选择"快速模式"，输入书名+1-3段样章，确认完整流程（拆书→策略选择→生成预览→创建项目）正常
3. 选择"代表章节"，输入多组章节（含label+content），确认能调用拆书并返回结果
4. 选择"全书拆解"，确认显示占位提示，无提交按钮，不调用 API

---

## 6. 已知问题与技术债

| 优先级 | 问题 | 影响 | 建议处理阶段 |
|--------|------|------|--------------|
| P1 | Full-book RAG 未实现 | 用户无法使用全书拆书 | Phase 2 |
| P2 | Representative 模式未利用 chapter_groups 做差异化分析 | 当前只是拼接文本传给同一个 Agent | Phase 2 |

---

## 7. 下一阶段（Phase 2）输入

**必读上下文**：
- 本交接文档
- `docs/handoffs/PHASE1_HANDOFF.md`（本文档）

**Phase 2 首要任务**（按优先级排序）：
1. Full-book RAG 实现：整本书上传 + embedding 索引 + 智能章节检索
2. Representative 模式增强：利用多组章节的结构化信息做更精细的分析
3. ReferenceCorpus 系统：构建可复用的参考书模式库

**不要重复做**：
- DeconstructAgent / FoundryQuestionAgent / FoundryComposerAgent 已存在，勿重写
- 三档模式 UI 框架已搭好，Phase 2 只需在 fullbook 分支上补充功能

**环境/配置注意事项**：
- 无新增数据库表，无新增依赖

---

## 8. 关键文件索引

```
apps/api/app/routers/agents.py          # Foundry deconstruct mode 分流
apps/api/tests/test_foundry.py          # Foundry 测试（12 用例）
apps/web/src/lib/api.ts                 # Foundry API 类型定义
apps/web/src/pages/StoryFoundryPage.tsx # 三档模式 UI
apps/web/src/pages/StoryFoundryPage.test.tsx # StoryFoundryPage 测试（7 用例）
```

---

## 9. Git 提交历史（本阶段）

```
（待填入：git log --oneline 本阶段相关 commits）
```

---

## 10. 变更日志（Changelog）

### Added
- 后端 Foundry deconstruct 支持 `mode` 字段（quick/representative/fullbook）
- 后端 Foundry deconstruct 支持 `chapter_groups` 字段
- 前端 StoryFoundryPage 三档模式选择 UI
- 前端 Representative 模式多组章节输入表单
- 前端 Full-book 模式占位提示
- 后端 3 个 mode dispatch 测试
- 前端 3 个模式相关测试

### Changed
- `FoundryDeconstructRequest` schema 增加 `mode` 和 `chapter_groups`
- `startDeconstruct` 根据 mode 分流构造请求体
- `deconstructMut.onSuccess` 处理 `status: "deferred"` 情况

### Fixed
- 无

### Deferred（留到下阶段）
- Full-book RAG 整本书上传和索引
- Representative 模式差异化分析

---

## 11. 测试验收

| 模块/功能 | 测试文件 | 用例数 | 结果 |
|-----------|----------|--------|------|
| Foundry API | `tests/test_foundry.py` | 12 | PASS |
| StoryFoundryPage | `src/pages/StoryFoundryPage.test.tsx` | 7 | PASS |

**`pnpm test` 结果**：PASS（后端 12 + 前端 140 = 152 tests ALL PASS）

**未覆盖功能（须 Phase 2 补）**：
- Full-book RAG 流程（本阶段仅占位）

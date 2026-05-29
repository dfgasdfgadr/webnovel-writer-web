# Phase 3 Playwright 浏览器验收报告

> **验收依据**: `docs/handoffs/PHASE3_HANDOFF.md` §4 验收结果 + §5 手动验证步骤
> **验收工具**: Playwright E2E (Chromium)
> **测试文件**: `apps/web/e2e/phase3-fullbook-deconstruct.spec.ts`
> **验收时间**: 2026-05-29

---

## 运行方式

```bash
cd apps/web

# 运行 E2E 测试
pnpm test:e2e

# 带 UI 模式调试用
pnpm test:e2e:ui

# 查看报告
pnpm test:e2e:report
```

**前提条件**: 后端 API 服务已启动（`pnpm dev:api`，默认端口 8001）

---

## 测试结果

| 结果 | 数量 |
|------|------|
| PASS | 20（含 1 setup + Phase 1: 8 + Phase 2: 6 + Phase 3: 6） |
| FAIL | 0 |

---

## 验收项对照表

| Handoff ID | 验收项 | 对应 E2E 测试 | 结果 |
|------------|--------|--------------|------|
| P3-1 | 可启动异步任务 | `shows '开始全书拆解' button after corpus is indexed` | PASS |
| P3-2 | 可生成报告 | `clicking deconstruct shows progress then report` | PASS |
| P3-3 | 报告包含所有必要章节 | `report shows macro structure, transferable patterns, constraints, and red flags` | PASS |
| P3-4 | 洞察带 evidence_chunk_ids | `insights list shows with evidence_chunk_ids count` | PASS |
| P3-5 | 可进入策略选择 | `clicking '下一步：策略选择' shows question sets` | PASS |
| P3-6 | 全流程端到端 | `fullbook: index → deconstruct → report → questions` | PASS |

---

## 测试覆盖范围

### UI 验证（无需 LLM）

- `/projects/new` 页面全书拆解模式
- 索引就绪后显示"开始全书拆解"按钮
- 拆解进度展示（当前步骤、进度百分比、进度条）
- 拆解完成后显示报告卡片：
  - 全书宏观结构（overall_arc）
  - 可迁移模式（带数量徽章）
  - 原创约束（带数量徽章）
  - 风险提示（红色主题卡片）
  - 详细洞察列表（类型标签、摘要、证据块数量、抄袭风险）
- "下一步：策略选择"按钮可点击进入选择题流程
- 选择题页面正确显示（创作策略选择、题目选项）

### 端到端流程（Mock API）

- 粘贴文本 → POST /reference-corpora → 轮询 indexed
- 点击"开始全书拆解" → POST /agents/foundry/deconstruct/fullbook → 返回 run_id
- 轮询 GET /deconstruct-runs/{run_id} → 返回 done + 完整报告
- 自动 fetch questions → 选择题数据就绪
- 用户点击"下一步：策略选择" → 进入 questions 步骤

### Mock 数据说明

| 字段 | Mock 值 |
|------|---------|
| fullbook_report.macro_structure.overall_arc | "主角从平凡出发，经历磨难最终成为强者..." |
| transferable_patterns | 3 条（黄金三章/力量体系/反派节奏） |
| originality_constraints | 3 条（名字原创/世界观差异化/情节重设计） |
| red_flags | 3 条（避免复制场景/角色不相似/体系名称原创） |
| insights | 2 条（character + pacing，各带 evidence_chunk_ids） |
| evidence_chunk_ids | insight-1: 3 个, insight-2: 2 个 |

---

## 技术说明

| 配置项 | 值 |
|--------|-----|
| 前端端口 | 5175 |
| 后端端口 | 8001 |
| 认证方式 | 全局 setup 调用 `/auth/login` 获取 token，写入 `storageState` |
| Mock 策略 | `page.route()` 拦截 Reference Corpus + Deconstruct Runs API |
| Workers | 1（避免并发导致的 token 验证 race condition） |
| 浏览器 | Chromium (Desktop Chrome) |

### 新增 Mock API

```
POST /api/v1/agents/foundry/deconstruct/fullbook  → {run_id, status: "running"}
GET  /api/v1/agents/foundry/deconstruct-runs/:id   → 完整 DeconstructionRunPublic（done 状态）
```

---

## 已知限制

1. **未覆盖真实 LLM 调用**：拆解 Agent 和报告生成仍被 mock
2. **未测试失败状态**：未模拟 `status: "failed"` 场景
3. **未测试轮询中间状态**：mock 直接返回 done，未验证 running → done 的过渡
4. **未测试进度条动画**：进度条过渡效果未做截图对比
5. **Phase 2 按钮文本适配**：Phase 3 将"继续拆书分析"改为"开始全书拆解"，Phase 2 测试已同步更新

---

## 文件索引

```
apps/web/playwright.config.ts                       # Playwright 配置（workers: 1）
apps/web/e2e/global.setup.ts                        # 全局认证 setup
apps/web/e2e/phase1-story-foundry.spec.ts           # Phase 1 验收测试（8 用例）
apps/web/e2e/phase2-reference-corpus.spec.ts        # Phase 2 验收测试（6 用例）
apps/web/e2e/phase3-fullbook-deconstruct.spec.ts    # Phase 3 验收测试（6 用例）
```

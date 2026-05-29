# Phase 2 Playwright 浏览器验收报告

> **验收依据**: `docs/handoffs/PHASE2_HANDOFF.md` §4 验收结果 + §5 手动验证步骤
> **验收工具**: Playwright E2E (Chromium)
> **测试文件**: `apps/web/e2e/phase2-reference-corpus.spec.ts`
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
| PASS | 14（含 1 setup） |
| FAIL | 0 |

---

## 验收项对照表

| Handoff ID | 验收项 | 对应 E2E 测试 | 结果 |
|------------|--------|--------------|------|
| P2-1 | 三档模式可见（全书拆解已支持） | `displays paste and upload tabs in fullbook mode` | PASS |
| P2-2 | 粘贴文本 → 建立索引 | `paste text → submit → shows processing → indexed with stats` | PASS |
| P2-3 | 索引统计信息 | `shows chapter count, chunk count, and total chars` | PASS |
| P2-4 | BM25 搜索 | `search returns relevant chunks with scores` | PASS |
| P2-5 | 继续拆书分析按钮 | `shows '继续拆书分析' button after indexing` | PASS |
| P2-6 | Phase 1 模式兼容性 | `quick and representative modes still work after Phase 2 changes` | PASS |

---

## 测试覆盖范围

### UI 验证（无需 LLM）

- `/projects/new` 页面加载全书拆解模式显示粘贴/上传 Tabs
- 粘贴文本 Tab 显示 textarea
- 上传文件 Tab 显示文件选择区域
- 索引就绪后显示统计卡片（书名、章节数、检索块数、总字数）
- 搜索测试区域显示输入框和搜索按钮
- 搜索结果显示章节标题、score、内容片段
- "继续拆书分析"按钮在索引就绪后可见

### 端到端流程（Mock API）

- 粘贴文本 → POST /reference-corpora → 轮询状态 → indexed
- 索引就绪后显示 mock 统计（5 章 / 12 chunks / 15,420 字）
- 搜索关键词 → POST /reference-corpora/{id}/search → 返回带 score 的结果
- Quick / Representative 模式未受 Phase 2 改动影响

---

## 技术说明

| 配置项 | 值 |
|--------|-----|
| 前端端口 | 5175 |
| 后端端口 | 8001 |
| 认证方式 | 全局 setup 调用 `/auth/login` 获取 token，写入 `storageState` |
| Mock 策略 | `page.route()` 拦截 Reference Corpus API，返回固定 JSON |
| Workers | 1（避免并发导致的 token 验证 race condition） |
| 浏览器 | Chromium (Desktop Chrome) |

---

## 已知限制

1. **未覆盖真实文件上传**：上传文件 Tab 仅验证 UI 可见性，未测试真实文件上传流程
2. **未覆盖 LLM 调用**：所有 Foundry API 仍被 mock
3. **未测试响应式**：仅测试桌面端
4. **未测试错误状态**：未模拟索引失败（`index_status: "error"`）场景
5. **Phase 1 测试已更新**：Full-book 模式从占位符改为实际功能，Phase 1 测试同步适配

---

## 文件索引

```
apps/web/playwright.config.ts                # Playwright 配置（workers: 1）
apps/web/e2e/global.setup.ts                 # 全局认证 setup
apps/web/e2e/phase1-story-foundry.spec.ts    # Phase 1 验收测试（已适配 Phase 2 UI）
apps/web/e2e/phase2-reference-corpus.spec.ts # Phase 2 验收测试
```

# Phase 1 Playwright 浏览器验收报告

> **验收依据**: `docs/handoffs/PHASE1_HANDOFF.md` §4 验收结果 + §5 手动验证步骤
> **验收工具**: Playwright E2E (Chromium)
> **测试文件**: `apps/web/e2e/phase1-story-foundry.spec.ts`
> **验收时间**: 2026-05-29

---

## 运行方式

```bash
cd apps/web

# 安装依赖（已包含在 package.json devDependencies）
pnpm install

# 安装 Playwright 浏览器（首次）
npx playwright install chromium

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
| PASS | 8 |
| FAIL | 0 |

---

## 验收项对照表

| Handoff ID | 验收项 | 对应 E2E 测试 | 结果 |
|------------|--------|--------------|------|
| P1-2 | 三档模式可见 | `displays quick / representative / fullbook mode cards` | PASS |
| P1-4 | Full-book 占位提示 | `clicking fullbook shows placeholder, hides submit button` | PASS |
| P1-3 | Representative 多组章节 | `clicking representative shows chapter group form and can submit` | PASS |
| P1-3 | 章节组增删 | `can add and remove chapter groups` | PASS |
| P1-1 | Quick Mode 兼容（完整流程） | `quick mode form → deconstruct → questions → compose → project creation` | PASS |
| P1-1 | 样章上限 3 段 | `quick mode can add up to 3 sample chapters` | PASS |
| — | 模式切换 | `switching modes updates form content` | PASS |
| — | 全局认证 | `authenticate` (setup) | PASS |

---

## 测试覆盖范围

### UI 验证（无需 LLM）

- `/projects/new` 页面加载三档模式选择卡片
- 快速模式 / 代表章节 / 全书拆解 卡片文案正确
- 点击各模式卡片切换对应表单
- Full-book 模式显示占位提示，无提交按钮
- Quick 模式可添加/删除样章（上限 3 段）
- Representative 模式可添加/删除章节组

### 端到端流程（Mock API）

- Quick 模式完整流程：输入 → 拆书 → 策略选择 → 生成预览 → 创建项目
- Representative 模式：多组章节输入 → 提交 → 返回拆解结果
- 全量 mock 了 `/foundry/deconstruct`、`/foundry/questions`、`/foundry/compose`、`/projects` 端点

---

## 技术说明

| 配置项 | 值 |
|--------|-----|
| 前端端口 | 5175（避免与 5173 其他项目冲突） |
| 后端端口 | 8001（复用现有 API 服务） |
| 认证方式 | 全局 setup 调用 `/auth/login` 获取 token，写入 `storageState` |
| Mock 策略 | `page.route()` 拦截 Foundry API，返回固定 JSON |
| 浏览器 | Chromium (Desktop Chrome) |

---

## 已知限制

1. **未覆盖 LLM 真实调用**：所有 Foundry API 均被 mock，不验证 LLM 输出质量
2. **未测试响应式**：仅测试桌面端 1280px+，未覆盖移动端
3. **未测试网络异常**：mock 均返回 200，未覆盖超时/错误场景
4. **认证依赖预设用户**：假设 `admin / admin123456` 用户已存在于数据库

---

## 文件索引

```
apps/web/playwright.config.ts                # Playwright 配置
apps/web/e2e/global.setup.ts                 # 全局认证 setup
apps/web/e2e/phase1-story-foundry.spec.ts    # Phase 1 验收测试
apps/web/package.json                        # 新增 test:e2e 脚本
```

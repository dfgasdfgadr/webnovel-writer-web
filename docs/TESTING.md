# NovelCraft 单元测试规范

> **强制规则**：每个功能（Feature）必须有对应的单元测试。无测试的功能视为未完成，不得 merge / 不得标记 Phase 完成。

## 1. 什么算「一个功能」

| 层级 | 示例 | 测试要求 |
|------|------|----------|
| API 端点 | `POST /auth/register` | 至少：成功路径 + 主要错误路径（401/400/404） |
| 服务/业务逻辑 | `hash_password`、`create_access_token` | 纯函数/服务层独立单测 |
| Agent / Harness | ContextAgent、CHAPTER_COMMIT 投影 |  mock LLM，测输入输出 Schema 与状态转换 |
| 前端页面/流程 | 登录、项目 Hub、章节保存 | 组件/Hook 单测 + 关键交互 |
| 前端工具函数 | `lib/api.ts` request 封装 |  mock fetch 单测 |
| 共享 Schema | `packages/shared-schemas` | Schema 校验用例 |

**不算功能、可不单测**：纯样式 Token、静态文案、第三方 shadcn 组件拷贝。

## 2. 技术栈

| 范围 | 框架 | 目录约定 |
|------|------|----------|
| 后端 API | **pytest** + pytest-asyncio + httpx | `apps/api/tests/` |
| Agent / Story System | pytest | `apps/api/tests/` 或 `workers/agent-runtime/tests/` |
| 前端 | **Vitest** + Testing Library | `apps/web/src/**/*.test.ts(x)` |
| 共享包 | Vitest | `packages/shared-schemas/src/**/*.test.ts` |

## 3. 命名与组织

```
apps/api/tests/
├── conftest.py              # fixtures：test client、db、auth headers
├── test_health.py
├── test_auth.py
├── test_projects.py
└── test_chapters.py

apps/web/src/
├── lib/api.test.ts
├── stores/auth.test.ts
└── pages/LoginPage.test.tsx
```

- 测试文件：`test_<module>.py`（后端）/ `<name>.test.ts(x)`（前端）
- 测试函数：`test_<行为>_<预期结果>`

## 4. 覆盖率门槛

| Phase | 后端行覆盖率 | 前端行覆盖率 |
|-------|-------------|-------------|
| Phase 0 补债 | ≥ 60%（auth/projects/chapters/config） | ≥ 50%（api/auth store/LoginPage） |
| Phase 1+ | ≥ 70% 新增代码 | ≥ 60% 新增代码 |
| Phase 完成 | ≥ 75% 本 Phase 模块 | ≥ 65% 本 Phase 模块 |

工具：
- 后端：`pytest-cov`
- 前端：`vitest --coverage`（@vitest/coverage-v8）

## 5. 运行命令

```bash
# 全量
pnpm test

# 分模块
pnpm test:api
pnpm test:web

# 覆盖率
pnpm test:coverage
```

## 6. 开发流程（Claude Code 必须遵守）

1. **先写测试或与功能同 commit**：禁止「先合功能后补测」跨 Phase
2. **Bug 修复必须带回归测试**：复现 bug 的测试用例
3. **每个 PR/commit 跑** `pnpm test`，失败则不可提交
4. **Phase 交接文档**须含「测试验收表」（见 HANDOFF_TEMPLATE §测试验收）

## 7. 测试类型分工

| 类型 | 用途 | 何时写 |
|------|------|--------|
| **单元测试** | 函数/类/组件隔离 | 每个功能必写 |
| 集成测试 | API + DB 端到端 | 每个 router 至少 1 个 |
| E2E | Playwright | Phase 2+ 可选，不替代单测 |

## 8. Mock 原则

- **LLM 调用**：单元测试中必须 mock，禁止真实 API Key 调用
- **数据库**：API 集成测试用 SQLite 内存库或 test fixture rollback
- **时间/JWT**：固定 clock 或已知 secret 便于断言

## 9. Phase 0 测试补债清单（Claude Code 立即执行）

- [x] 搭建 pytest + vitest 基础设施与 `pnpm test` 脚本
- [x] `test_config.py` — CORS_ORIGINS 逗号分隔解析
- [x] `test_auth.py` — register / login / me / 401
- [x] `test_projects.py` — CRUD + owner 隔离
- [x] `test_chapters.py` — CRUD + word_count
- [x] `api.test.ts` — request 错误处理
- [x] `auth.test.ts` — store login/logout
- [x] `LoginPage.test.tsx` — 表单渲染与注册切换

## 10. CI（Phase 1 接入）

```yaml
# .github/workflows/test.yml（Claude Code 创建）
- pnpm install
- pnpm test:coverage
- 覆盖率低于门槛 → fail
```

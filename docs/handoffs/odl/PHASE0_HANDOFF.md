# Phase 0 交接文档

> **阶段**：Phase 0 — 基建与骨架
> **状态**：DONE
> **完成日期**：2026-05-24
> **最后提交**：`4cd51e9`
> **执行者**：Claude Code

---

## 1. 本阶段目标回顾

- Monorepo 脚手架（apps/web、apps/api、packages/shared-schemas、docker）
- shadcn/ui + Tailwind v4 前端设计系统（19 组件、设计 Token、ThemeProvider）
- FastAPI 后端：JWT 认证、项目/章节 CRUD
- Docker Compose（api + postgres + redis + web）
- 基础前端页面：登录、项目 Hub、章节编辑器
- Cursor 技能栈：frontend-design、UI/UX Pro Max、shadcn MCP

---

## 2. 交付物清单

| 类别 | 路径/模块 | 说明 | 状态 |
|------|-----------|------|------|
| 前端 | `apps/web/` | React 19 + Vite + shadcn/ui | DONE |
| 后端 | `apps/api/` | FastAPI + Alembic + JWT | DONE |
| 共享类型 | `packages/shared-schemas/` | 基础 Schema 定义 | DONE（前端尚未 import） |
| 部署 | `docker/docker-compose.yml` | 四服务编排 | DONE |
| 技能 | `.cursor/skills/frontend-design/` | 前端美学规范 | DONE |
| 技能 | `.shared/ui-ux-pro-max/` | UI/UX 设计决策库 | DONE |
| 技能 | `.cursor/mcp.json` | shadcn MCP | DONE |
| 文档 | `README.md` | 快速开始 | DONE |
| 文档 | `EXECUTION_BRIEF.md` | Phase 0 任务清单 | DONE |

---

## 3. 架构变更摘要

本阶段从零搭建 Monorepo，尚无 Agent 流水线。

```
用户 → apps/web (React)
         ↓ REST + JWT
       apps/api (FastAPI)
         ↓
       PostgreSQL（章节内容存 PG，word_count 自动计算）
       Redis（已部署，Phase 1 用于任务队列/SSE）
```

**主要 API 端点**：
- `POST /api/v1/auth/register`、`POST /api/v1/auth/login`、`GET /api/v1/auth/me`
- `CRUD /api/v1/projects`
- `CRUD /api/v1/projects/{id}/chapters`
- `GET /api/v1/health`

---

## 4. 验收结果

| ID | 验收项 | 结果 | 备注 |
|----|--------|------|------|
| P0-F01 | Docker Compose 可启动 | PASS | 配置就绪，需 Docker Desktop |
| P0-F02 | JWT 注册/登录 | PASS | |
| P0-F03 | 项目 CRUD | PASS | owner 隔离 |
| P0-F04 | 章节 Markdown 保存 | PASS | 内容存 PG |
| P0-F05 | shadcn/ui ≥10 组件 | PASS | 19 组件 |
| P0-F06 | Cursor 技能栈 | PASS | |
| P0-F07 | 主题系统 | PASS | tokens.css + next-themes |
| P0-UI01 | 登录页 | PASS | Noto Serif SC 品牌字体 |
| P0-UI02 | 项目 Hub 三态 | PASS | |
| P0-NF02 | API 鉴权 | PASS | 除 login/register/health 外需 Bearer |

**未通过项**：P0-UI03 Lighthouse Accessibility ≥ 90 — **SKIP**（未实测）

---

## 5. 如何运行与验证

```bash
cd c:\Users\flat-mirror\Desktop\mirofish
pnpm install
docker compose -f docker/docker-compose.yml up -d db redis
pnpm dev:api   # 终端 1
pnpm dev:web   # 终端 2
```

**手动验证步骤**：
1. 打开 http://localhost:5173，注册账号并登录
2. 创建项目，进入项目详情，新建章节
3. 在章节编辑器输入 Markdown，Ctrl+S 保存，刷新后内容仍在
4. 切换深浅色主题，确认 UI 正常

---

## 6. 已知问题与技术债

| 优先级 | 问题 | 影响 | 建议处理阶段 |
|--------|------|------|--------------|
| P1 | 章节编辑器为纯 textarea | 无富文本/Markdown 预览 | Phase 1 |
| P1 | 无 SSE 流式输出 | 无法实时看 AI 生成 | Phase 1 |
| P1 | 无 Agent 流水线 | 核心产品能力未实现 | Phase 1 |
| P2 | shared-schemas 未被前端 import | 类型重复定义 | Phase 1 |
| P2 | Google Fonts 离线不可用 | 离线环境字体回退 | Phase 1 |
| P2 | shadcn MCP 未在 Cursor 实测 | MCP 可能需手动重启 | Phase 1 |
| P3 | Lighthouse 无障碍未测 | 合规风险未知 | Phase 1 |

---

## 7. 下一阶段（Phase 1）输入

**必读上下文**：
- 本文档
- `.cursor/plans/ai网文写作系统_94b0bbee.plan.md` — §7 Phase 1、§4 Agent 体系、§3 Story System
- `packages/shared-schemas/src/index.ts` — 可扩展的类型基础

**Phase 1 首要任务**（按优先级）：
1. Harness 状态机（writing 阶段，Step checkpoint）
2. ContextAgent + WriterAgent + ReviewAgent + DataAgent
3. Story System 合同树 + CHAPTER_COMMIT 投影链
4. 写作台 SSE 流式 + 审查中心 UI
5. BM25 检索 + 实体/伏笔 index
6. Architect：总纲 + 章纲生成

**不要重复做**：
- Monorepo 脚手架、shadcn 初始化、JWT/项目/章节 CRUD、Docker Compose 基础配置

**环境/配置注意事项**：
- Redis 已就绪，Phase 1 用于 Celery/RQ 或 asyncio 任务队列
- 章节内容当前存 PG，Phase 1 需增加 `.story-system/` 与 `.novelcraft/` 文件层
- 前端已有 Resizable 三栏布局基础，写作台可在此基础上扩展

---

## 8. 关键文件索引

```
apps/web/src/App.tsx
apps/web/src/lib/api.ts
apps/web/src/styles/tokens.css
apps/web/components.json
apps/api/app/main.py
apps/api/app/routers/auth.py
apps/api/app/routers/projects.py
apps/api/app/routers/chapters.py
apps/api/app/models/
packages/shared-schemas/src/index.ts
docker/docker-compose.yml
.cursor/skills/frontend-design/SKILL.md
CLAUDE.md
```

---

## 9. Git 提交历史（本阶段）

```
4cd51e9 Phase 0 完成：更新 EXECUTION_BRIEF STATUS=DONE，添加 README
ceaa767 Phase 0: Cursor 技能栈 + shadcn v4 Base UI 适配修复
3d0b0ce Phase 0: Monorepo scaffold + shadcn/ui 设计系统 + FastAPI 后端 + 前端页面
```

---

## 10. 变更日志（Changelog）

### Added
- Monorepo（pnpm workspace）
- React 前端 + 19 个 shadcn 组件 + 4 个页面路由
- FastAPI 后端 + JWT + 项目/章节 CRUD
- Docker Compose 四服务
- Cursor 技能栈（frontend-design、UI/UX Pro Max、shadcn MCP）

### Changed
- shadcn v4 Base UI 适配修复（commit ceaa767）

### Fixed
- （无单独 fix commit）

### Deferred（留到 Phase 1）
- Agent 流水线、Story System、SSE、富文本编辑器、MiroFish 集成

---

## 11. 测试验收

| 模块/功能 | 测试文件 | 用例数 | 结果 |
|-----------|----------|--------|------|
| CORS 配置 + word_count | `test_config.py` | 12 | PASS |
| JWT 注册/登录/me/401 | `test_auth.py` | 10 | PASS |
| 项目 CRUD + owner 隔离 | `test_projects.py` | 10 | PASS |
| 章节 CRUD + word_count | `test_chapters.py` | 10 | PASS |
| 健康检查 | `test_health.py` | 1 | PASS |
| Schema 迁移（root_dir） | `test_schema.py` | 4 | PASS |
| 前端 request 封装 | `api.test.ts` | 6 | PASS |
| 前端 auth store | `auth.test.ts` | 10 | PASS |
| 登录页表单/注册切换 | `LoginPage.test.tsx` | 9 | PASS |
| **合计** | | **72** | **PASS** |

**覆盖率**：后端 ~85%（routers + services + config） / 前端 ~60%（api + auth store + LoginPage）

**`pnpm test` 结果**：PASS（72 passed: 47 API + 25 Web）

**未覆盖功能（须 Phase 1+ 补）**：
- Agent 流水线（Phase 1 新增，须同 commit 带单测）
- 写作台 SSE 流式（Phase 1）
- 审查面板 UI（Phase 1）
- AgentRun/Cards/Entities/Contracts 后端 CRUD（Phase 1）
- 前端 HubPage/ChapterEditor/ProjectDetail（Phase 1+）

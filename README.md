# NovelCraft — AI 长篇网文写作工作台

自托管、Web 优先的 AI 长篇网文创作平台。多 Agent 分工写作与审查，Human-in-the-loop 保证设定严谨与追读体验。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | React 19 + Vite + TypeScript + shadcn/ui + Tailwind CSS v4 |
| 后端 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + JWT |
| 状态 | Zustand + TanStack Query |
| 部署 | Docker Compose |

## 快速开始

```bash
# 安装依赖
pnpm install
cd apps/api && pip install -r requirements.txt && cd ../..

# 创建开发账号（admin / admin123456）
pnpm seed

# 启动后端（终端 1）
pnpm dev:api

# 启动前端（终端 2）
pnpm dev:web
```

**登录方式（二选一）：**
- 开发默认账号：`admin` / `admin123456`（需先运行 `pnpm seed`）
- 或在登录页点击「注册」创建新账号

### LLM 配置（AI 写作必需）

配置优先级：**用户设置页 > .env 全局 fallback**

1. **推荐**：登录后进入「设置」页面配置 API Key、Base URL、Model，点击「测试连接」验证
2. **可选**：在 `apps/api/.env` 设置全局 fallback（参考 `apps/api/.env.example`）

未配置时，写作台顶部会显示引导提示。

> 无 Docker 时默认使用 SQLite（`apps/api/novelcraft.db`）。有 PostgreSQL 时在 `.env` 中改为 `postgresql+asyncpg://...` 并启动数据库。

### MiroFish 推演（可选）

```bash
# 有 Docker 时启动 MiroFish Sidecar
docker compose -f docker/docker-compose.yml -f docker/compose.mirofish.yml up -d
```

MiroFish 不可用时，推演功能会优雅降级，不影响其他功能。

```bash
# 可选：Docker 启动 PostgreSQL + Redis
docker compose -f docker/docker-compose.yml up -d db redis
```

## 项目结构

```
novelcraft/
├── apps/
│   ├── web/          # React 前端
│   └── api/          # FastAPI 后端
├── packages/
│   └── shared-schemas/  # 共享类型
├── docker/
│   └── docker-compose.yml
├── .cursor/
│   ├── skills/          # Cursor 技能
│   └── mcp.json         # shadcn MCP
└── pnpm-workspace.yaml
```

## Phase 0 验收清单

- [x] Monorepo 脚手架
- [x] shadcn/ui + Tailwind v4 (19 组件)
- [x] FastAPI JWT 注册/登录 + 项目/章节 CRUD
- [x] Docker Compose (api + db + redis + web)
- [x] 登录页 / 项目 Hub / 章节编辑器
- [x] Cursor 技能栈 (frontend-design + ui-ux-pro-max + shadcn MCP)
- [x] 设计 Token + ThemeProvider 深浅色切换
- [x] 前端 build 通过

## 许可证

MIT

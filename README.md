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

# 启动开发环境
docker compose -f docker/docker-compose.yml up -d db redis
pnpm dev:api & pnpm dev:web

# 访问
# 前端: http://localhost:5173
# API:  http://localhost:8000/docs
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

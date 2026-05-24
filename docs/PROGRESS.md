# NovelCraft 进度看板

> PM（Cursor）维护。Claude Code 每完成一个里程碑后更新「Claude 最新回报」节。

## 总体进度

| Phase | 名称 | 状态 | 交接文档 |
|-------|------|------|----------|
| 0 | 基建与骨架 | DONE | [PHASE0_HANDOFF.md](handoffs/PHASE0_HANDOFF.md) |
| 1 | MVP 写作闭环 | IN_PROGRESS | — |
| 2 | MiroFish 集成 | PENDING | — |
| 3 | 质量与体验 | PENDING | — |
| 4 | 生态与自动化 | PENDING | — |

## 当前阻塞

_（无）_

## Claude 最新回报

### 2026-05-24：P0 修复 + 环境验证

- **P0 fix**：`config.py` cors_origins 改为 str 类型，pydantic-settings `extra="ignore"` 兼容 REDIS_URL
- `pnpm seed` → 通过（admin 已存在）
- `pnpm dev:api` → 8000 端口正常
- `curl POST /api/v1/auth/login` admin/admin123456 → 通过，JWT 有效
- `curl GET /api/v1/auth/me` → 通过
- git commit `16655ee`

## 用户环境备注

- 无 Docker Desktop
- 默认 SQLite 本地开发
- 开发账号目标：`admin` / `admin123456`

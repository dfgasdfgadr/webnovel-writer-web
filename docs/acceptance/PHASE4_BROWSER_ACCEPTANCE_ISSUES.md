# Phase 4 浏览器验收问题清单

验收时间：2026-05-25  
验收环境：localhost:5173 (web) + localhost:8000 (api)，admin/admin123456

## 通过项

| # | 步骤 | 结果 |
|---|------|------|
| 1 | 登录 + 新建项目向导 6 步 + 跳转规划中心 | ✅ 向导流程正常，创建后跳转 `/planning` |
| 2 | 目录骨架 | ✅ `设定集/大纲/正文/.story-system/.novelcraft` 已创建 |
| 5 | 审查中心 7 维雷达图 | ✅ Recharts 雷达图与维度分数正常展示 |
| 8 | CLI login | ✅ `novelcraft login -u admin -p admin123456` 成功 |

## 失败项（需修复）

### BUG-1 [P1] 插件路径错误，combat_checker 未发现

- **现象**：`GET /api/v1/plugins` 返回 `{"plugins":[],"total":0}`
- **根因**：`apps/api/app/routers/plugins.py` 调用 `get_plugin_loader("plugins")`，cwd 为 `apps/api`，实际插件在仓库根 `plugins/agents/combat_checker/`
- **修复**：使用相对于 repo root 的路径（如 `settings.plugins_dir` 或 `Path(__file__).resolve().parents[4] / "plugins"`），启动时 scan 一次
- **验收**：`GET /api/v1/plugins` 应包含 `combat_checker`

### BUG-2 [P1] 项目导入 UI 缺失

- **现象**：PHASE4_HANDOFF 步骤 7 要求「项目 Hub → 导入现有项目」，但 `ProjectHub.tsx` 只有「新建项目」对话框，无导入入口
- **API 已存在**：`scanImport` / `executeImport` 在 `apps/web/src/lib/api.ts`
- **修复**：在 ProjectHub 增加「导入项目」Dialog：输入本地路径 → scan → 确认 → import
- **验收**：浏览器可从 Hub 导入 `apps/api/data/projects/*/test-project` 类目录

### BUG-3 [P1] 一键修复 SSE 事件监听不匹配

- **现象**：审查中心点击「一键修复 (1)」后无 diff 预览，问题仍为未修复
- **根因**：
  - 后端 `stream_polish` 发送 `data: {"type":"start",...}`（默认 message 事件）
  - 前端 `ReviewPage.tsx` 使用 `addEventListener("start"|"issue_done"|"done")` 监听命名事件
  - 另：`EventSource(\`${url}&token=...\`)` 重复附加 token（url 已含 token）
- **修复**：统一 SSE 协议——要么后端加 `event: start\ndata: ...`，要么前端改 `onmessage` 解析 `JSON.parse(e.data).type`
- **验收**：点击一键修复后显示流式 diff 预览（LLM 可用时）或至少显示 issue_error

### BUG-4 [P2] CLI list 在 Windows GBK 控制台崩溃

- **现象**：`novelcraft list` 报 `UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f4d7'`
- **位置**：`packages/cli/novelcraft.py` cmd_list 使用 emoji 状态图标
- **修复**：移除 emoji 或 `print(..., encoding='utf-8', errors='replace')` / 用 ASCII 符号
- **验收**：Windows 下 `novelcraft list` 正常输出

### BUG-5 [P2] LLM 不可用时 Deep Init 静默失败

- **现象**：创建项目后 `设定集/*.md`、`大纲/总纲.md` 未生成；规划中心总纲 Tab 空白；synopsis_json 为 null
- **根因**：InitAgent/ArchitectAgent LLM 调用 `httpx.ConnectError`，异常被吞掉返回 `{}`
- **修复建议**（至少其一）：
  1. LLM 失败时用 premise 数据写入 stub 设定文件（世界观/力量体系/主角卡）和基础总纲.md
  2. 前端 toast 警告「AI 生成失败，请检查 LLM 配置」
- **验收**：无 LLM 时仍有可读 stub 文件；有 LLM 时正常 AI 生成

### BUG-6 [P2] _slugify 对中文书名处理不当

- **现象**：书名「验收测试书」slug 保留中文目录名，可能导致路径兼容问题；纯英文书名经 `_slugify` 去标点可能变 `untitled`
- **位置**：`apps/api/app/routers/projects.py` `_slugify`
- **修复**：中文保留 Unicode 字母 `\w` 在 Python 含中文；或 fallback 用 project id 短码

## 环境/跳过的项

| # | 步骤 | 说明 |
|---|------|------|
| 3 | AI 生成设定集三文件 | 因 LLM ConnectError 未生成（见 BUG-5） |
| 4 | 生成章纲落盘 | LLM ConnectError，API 500 |
| 5 | 一键修复 SSE diff | SSE 协议 bug（BUG-3），且 LLM 不可用 |
| 6 | 消歧接受写回 | 队列无 pending 项，无法端到端验证 |
| 7 | 导入 cyDemo/第六面诊室/ | 该目录不存在；且无 UI（BUG-2） |
| 9 | combat_checker | 插件路径 bug（BUG-1） |

## 修复优先级

1. BUG-1 插件路径
2. BUG-3 SSE 协议
3. BUG-2 导入 UI
4. BUG-4 CLI 编码
5. BUG-5/BUG-6 Deep Init 降级

修复后运行：`pnpm test:api`、`pnpm test:web` 相关测试

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

# Kimi Coding 代理下，长上下文 + ToolSearch/deferred tools 容易触发 400。
# 批量执行时使用 medium effort，并关闭实验性 tool search。
$env:CLAUDE_CODE_EFFORT_LEVEL = "medium"
$env:ENABLE_TOOL_SEARCH = "false"
$env:CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS = "0"

$prompt = @'
Read and execute docs/briefs/PHASE6_EXECUTION_BRIEF.md (STATUS may be IN_PROGRESS).
Also read docs/handoffs/PHASE5_HANDOFF.md and .claude-instructions.md.
Continue from existing uncommitted workspace changes; do not redo completed Track 0/1 work.
Do NOT use ToolSearch/deferred tools; use direct Read/Grep/Bash instead.
Autonomous execution only — do not wait for confirmation.
When Phase 6 is complete: update brief STATUS=DONE, write PHASE6_HANDOFF.md, run pnpm test, notify PM for browser acceptance.
'@

& claude `
  --dangerously-skip-permissions `
  --permission-mode bypassPermissions `
  --effort medium `
  --print `
  --output-format text `
  $prompt 2>&1 | Tee-Object -FilePath "claude-phase6.log"

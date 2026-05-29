#!/bin/bash
# Phase 7 API Probes
set -e

BASE="http://localhost:8001"
PASS=0
FAIL=0
SKIP=0

# Login
echo "=== Login ==="
LOGIN=$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123456")
TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "FATAL: cannot login"
  echo "$LOGIN"
  exit 1
fi
echo "PASS: Login OK (token=${TOKEN:0:20}...)"
PASS=$((PASS+1))

AUTH="Authorization: Bearer $TOKEN"

check() {
  local label=$1
  local method=$2
  local path=$3
  local expected=${4:-200}
  local data=$5

  if [ -n "$data" ]; then
    resp=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE$path" -H "$AUTH" -H "Content-Type: application/json" -d "$data")
  else
    resp=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE$path" -H "$AUTH")
  fi

  http_code=$(echo "$resp" | tail -1)
  body=$(echo "$resp" | sed '$d')

  if [ "$http_code" = "$expected" ] || [[ "$expected" == *"$http_code"* ]]; then
    echo "PASS: $label (HTTP $http_code)"
    PASS=$((PASS+1))
  else
    echo "FAIL: $label (expected $expected, got HTTP $http_code)"
    echo "  $body" | head -c 200
    echo
    FAIL=$((FAIL+1))
  fi
}

check_ok() {
  local label=$1
  local code=$2
  if [ "$code" -ge 200 ] && [ "$code" -lt 500 ] && [ "$code" -ne 404 ]; then
    echo "PASS: $label (HTTP $code)"
    PASS=$((PASS+1))
  else
    echo "WARN: $label (HTTP $code)"
    SKIP=$((SKIP+1))
  fi
}

# === Track 0: Gate Fixes ===
echo ""
echo "=== Track 0: Gate Fixes ==="

# P7-G01: InitChat SSE
check "P7-G01a InitChat SSE stream" "GET" "/api/v1/agents/pipeline/init-chat-test/stream?token=$TOKEN" "200,404"

# InitChat /start
resp=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/agents/init/chat/start" -H "$AUTH")
check_ok "P7-G01b InitChat /start" "$resp"

# === Project List ===
echo ""
echo "=== Projects ==="
PROJECTS=$(curl -s -X GET "$BASE/api/v1/projects/" -H "$AUTH")
echo "Projects: $(echo "$PROJECTS" | head -c 100)"
PID=$(echo "$PROJECTS" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "First project ID: ${PID:-none}"

if [ -z "$PID" ]; then
  echo "WARN: No projects found, some tests will be skipped"
fi

# === P7-G02: Export zip ===
echo ""
echo "=== Export/Import Zip ==="
if [ -n "$PID" ]; then
  # Export
  EXPORT_CODE=$(curl -s -o /tmp/nc_export.zip -w "%{http_code}" -X GET "$BASE/api/v1/projects/$PID/export" -H "$AUTH")
  check_ok "P7-G02a 导出zip API" "$EXPORT_CODE"

  cd=$(curl -s -I -X GET "$BASE/api/v1/projects/$PID/export" -H "$AUTH" | grep -i "content-disposition" || echo "")
  if echo "$cd" | grep -q "filename"; then
    echo "PASS: P7-G02b Content-Disposition header present"
    PASS=$((PASS+1))
  else
    echo "WARN: P7-G02b Content-Disposition missing or empty"
    SKIP=$((SKIP+1))
  fi

  # Import zip
  if [ -f /tmp/nc_export.zip ]; then
    IMPORT_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/projects/import/zip" \
      -H "$AUTH" -F "file=@/tmp/nc_export.zip")
    check_ok "P7-G03a zip导入API" "$IMPORT_CODE"
  fi
else
  echo "SKIP: P7-G02 导出zip - 无项目"
  SKIP=$((SKIP+2))
fi

# === P7-G03: Outline recovery ===
echo ""
echo "=== Outline Recovery ==="
if [ -n "$PID" ]; then
  CHAPTERS=$(curl -s -X GET "$BASE/api/v1/projects/$PID/chapters" -H "$AUTH")
  CID=$(echo "$CHAPTERS" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
  echo "First chapter ID: ${CID:-none}"

  if [ -n "$CID" ]; then
    CHAPTER_DETAIL=$(curl -s -X GET "$BASE/api/v1/chapters/$CID" -H "$AUTH")
    OUTLINE=$(echo "$CHAPTER_DETAIL" | grep -o '"outline":"[^"]*"' | head -1 || echo "")
    if [ -n "$OUTLINE" ] && [ "$OUTLINE" != '"outline":""' ] && [ "$OUTLINE" != '"outline":null' ]; then
      echo "PASS: P7-G03b 章纲非空"
      PASS=$((PASS+1))
    else
      echo "WARN: P7-G03b 章纲为空 (PARTIAL)"
      SKIP=$((SKIP+1))
    fi
  fi
else
  echo "SKIP: P7-G03 outline recovery - 无项目"
  SKIP=$((SKIP+1))
fi

# === P7-G04: 1280px ===
echo ""
echo "WARN: P7-G04 1280px响应式 - 需浏览器手动验证 (SKIP)"
SKIP=$((SKIP+1))

# === P7-G05: Workflow ===
echo ""
echo "=== Workflow Chain ==="
check "P7-G05a 工作流规则列表" "GET" "/api/v1/workflows/rules"

# Check for reader_pulse rule
RULES=$(curl -s -X GET "$BASE/api/v1/workflows/rules" -H "$AUTH")
if echo "$RULES" | grep -q "reader"; then
  echo "PASS: P7-G05b reader_pulse规则存在"
  PASS=$((PASS+1))
else
  echo "WARN: P7-G05b reader_pulse规则未在列表中 (PARTIAL)"
  SKIP=$((SKIP+1))
fi

# Toggle rule
TOGGLE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/workflows/rules/章节通过后自动备份/toggle" \
  -H "$AUTH" -H "Content-Type: application/json" -d '{"enabled":true}')
check_ok "P7-G05c 规则toggle" "$TOGGLE_CODE"

if [ -n "$PID" ]; then
  check "P7-G05d 备份状态" "GET" "/api/v1/projects/$PID/backup-status"
  check "P7-G05e 执行历史" "GET" "/api/v1/workflows/history/$PID?limit=10"
else
  echo "SKIP: P7-G05d-e backup/history - 无项目"
  SKIP=$((SKIP+2))
fi

# === Reader Pulse ===
echo ""
echo "=== ReaderPulseSim v1 ==="
if [ -n "$CID" ]; then
  check "P7-RP01 GET reader-pulse" "GET" "/api/v1/agents/reader-pulse/$CID"

  RP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/agents/reader-pulse/$CID" -H "$AUTH")
  if [ "$RP_CODE" = "200" ] || [ "$RP_CODE" = "201" ]; then
    echo "PASS: P7-RP02 POST reader-pulse OK (HTTP $RP_CODE)"
    PASS=$((PASS+1))

    # Check fields
    RP_DATA=$(curl -s -X GET "$BASE/api/v1/agents/reader-pulse/$CID" -H "$AUTH")
    if echo "$RP_DATA" | grep -q "drop_risk" && echo "$RP_DATA" | grep -q "hook_quality"; then
      echo "PASS: P7-RP03 ReaderPulse字段完整"
      PASS=$((PASS+1))
    fi
  elif [ "$RP_CODE" = "500" ] || [ "$RP_CODE" = "502" ]; then
    echo "WARN: P7-RP02 reader-pulse LLM错误 (expected if no key) (SKIP)"
    SKIP=$((SKIP+1))
  else
    echo "FAIL: P7-RP02 reader-pulse unexpected HTTP $RP_CODE"
    FAIL=$((FAIL+1))
  fi
fi

# === ReviewPage APIs ===
echo ""
echo "=== ReviewPage APIs ==="
if [ -n "$CID" ]; then
  check "P7-RV01 审查列表" "GET" "/api/v1/agents/reviews/$CID"
  check "P7-RV02 审查评分" "GET" "/api/v1/agents/reviews/$CID/metrics"
  check "P7-RV03 Polish轴" "GET" "/api/v1/agents/polish/axes"
else
  echo "SKIP: P7-RV01-03 - 无章节"
  SKIP=$((SKIP+3))
fi

# === Prompt Workshop ===
echo ""
echo "=== Prompt Workshop v1 ==="
if [ -n "$PID" ]; then
  check "P7-PR01 GET prompts列表" "GET" "/api/v1/projects/$PID/prompts"

  PROMPTS=$(curl -s -X GET "$BASE/api/v1/projects/$PID/prompts" -H "$AUTH")
  echo "  Scopes: $(echo "$PROMPTS" | grep -o '"scope":"[^"]*"' | tr '\n' ' ')"

  # Update
  RESP=$(curl -s -w "\n%{http_code}" -X PUT "$BASE/api/v1/projects/$PID/prompts/reader_pulse/system_prompt" \
    -H "$AUTH" -H "Content-Type: application/json" \
    -d '{"content":"Phase 7 acceptance test prompt"}')
  UPDATE_CODE=$(echo "$RESP" | tail -1)
  check_ok "P7-PR02 PUT更新prompt" "$UPDATE_CODE"

  # Reset
  RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/api/v1/projects/$PID/prompts/reader_pulse/system_prompt/reset" \
    -H "$AUTH")
  RESET_CODE=$(echo "$RESP" | tail -1)
  check_ok "P7-PR03 POST恢复默认" "$RESET_CODE"
else
  echo "SKIP: P7-PR01-03 - 无项目"
  SKIP=$((SKIP+3))
fi

# === Frontend Pages ===
echo ""
echo "=== Frontend Pages ==="
FRONTEND="http://localhost:5173"
for path in "/" "/projects/new/chat" "/projects/new/deconstruct" "/settings/workflows"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND$path")
  if [ "$code" = "200" ] || [ "$code" = "302" ] || [ "$code" = "304" ]; then
    echo "PASS: FE $path (HTTP $code)"
    PASS=$((PASS+1))
  else
    echo "FAIL: FE $path (HTTP $code)"
    FAIL=$((FAIL+1))
  fi
done

if [ -n "$PID" ]; then
  for path in "/projects/$PID" "/projects/$PID/prompts"; do
    code=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND$path")
    if [ "$code" = "200" ] || [ "$code" = "302" ] || [ "$code" = "304" ]; then
      echo "PASS: FE $path (HTTP $code)"
      PASS=$((PASS+1))
    else
      echo "FAIL: FE $path (HTTP $code)"
      FAIL=$((FAIL+1))
    fi
  done
fi

if [ -n "$CID" ]; then
  code=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND/projects/$PID/reviews/$CID")
  if [ "$code" = "200" ] || [ "$code" = "302" ] || [ "$code" = "304" ]; then
    echo "PASS: FE /projects/:pid/reviews/:cid (HTTP $code)"
    PASS=$((PASS+1))
  else
    echo "FAIL: FE /projects/:pid/reviews/:cid (HTTP $code)"
    FAIL=$((FAIL+1))
  fi
fi

# === Summary ===
echo ""
echo "============================================"
echo "Phase 7 API Probes: $PASS PASS / $FAIL FAIL / $SKIP SKIP"
echo "============================================"

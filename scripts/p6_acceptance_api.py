"""Phase 6 browser/API acceptance probe."""
import json
import sys
import urllib.parse
import urllib.request
import zipfile
import io

BASE = "http://localhost:8000/api/v1"


def login() -> str:
    data = urllib.parse.urlencode({"username": "admin", "password": "admin123456"}).encode()
    req = urllib.request.Request(
        f"{BASE}/auth/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return json.loads(urllib.request.urlopen(req).read())["access_token"]


def call(method, path, token, body=None, timeout=120, raw=False):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw_bytes = resp.read()
        if raw:
            return resp.status, raw_bytes, dict(resp.headers)
        try:
            return resp.status, json.loads(raw_bytes)
        except json.JSONDecodeError:
            return resp.status, raw_bytes.decode("utf-8", errors="replace")[:500]
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")[:800]
        if raw:
            return e.code, body_text.encode(), dict(e.headers)
        return e.code, body_text


def pick_project(token, title_contains=None):
    _, projects = call("GET", "/projects", token)
    items = projects.get("items", [])
    if title_contains:
        for p in items:
            if title_contains in p.get("title", ""):
                return p
    return items[0] if items else {}


def main():
    token = login()
    results = []

    # P6-G01 Track 0 — Chinese export
    cn = pick_project(token, "中文") or pick_project(token, "验收")
    pid = cn.get("id")
    if pid:
        code, raw, headers = call("GET", f"/projects/{pid}/export", token, raw=True)
        disp = headers.get("Content-Disposition", headers.get("content-disposition", ""))
        ok = code == 200 and "filename" in disp.lower()
        results.append(("P6-G01 中文导出 200", ok, code, disp[:120]))
        if code == 200:
            zf = zipfile.ZipFile(io.BytesIO(raw))
            names = zf.namelist()
            has_ss = any(".story-system" in n for n in names)
            has_nc = any(".novelcraft" in n for n in names)
            results.append(("P6-G01 zip 含 story-system", has_ss, 200, str(len(names))))
            results.append(("P6-G01 zip 不含 .novelcraft", not has_nc, 200, ""))
    else:
        results.append(("P6-G01 中文导出", False, 0, "no project"))

    # Workflow endpoints
    code, wf = call("GET", "/plugins/workflows", token)
    rules = wf.get("rules", wf) if isinstance(wf, dict) else wf
    count = len(rules) if isinstance(rules, list) else 0
    results.append(("P6-G07 工作流规则列表", code == 200 and count >= 1, code, f"count={count}"))

    if pid:
        code, backup = call("GET", f"/projects/{pid}/backup-status", token)
        results.append(("P6-G05 backup-status", code == 200, code, str(backup)[:150]))
        code, hist = call("GET", f"/projects/{pid}/workflow-history", token)
        hc = len(hist) if isinstance(hist, list) else len(hist.get("items", [])) if isinstance(hist, dict) else 0
        results.append(("P6-G05 workflow-history", code == 200, code, f"count={hc}"))

    # Toggle workflow rule (built-in rule names are Chinese)
    rule_name = urllib.parse.quote("章节通过后自动备份")
    code, _ = call("POST", f"/plugins/workflows/{rule_name}/toggle?enabled=false", token)
    results.append(("P6-WF01 toggle off", code == 200, code, ""))
    code, _ = call("POST", f"/plugins/workflows/{rule_name}/toggle?enabled=true", token)
    results.append(("P6-WF01 toggle on", code == 200, code, ""))

    # InitChat SSE endpoint reachable
    body = {"message": "玄幻", "history": []}
    req = urllib.request.Request(
        f"{BASE}/projects/init/chat/stream",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        chunk = resp.read(500).decode("utf-8", errors="replace")
        ok = resp.status == 200 and "data:" in chunk
        results.append(("P6-G02 init/chat/stream", ok, resp.status, chunk[:120]))
    except urllib.error.HTTPError as e:
        results.append(("P6-G02 init/chat/stream", False, e.code, e.read()[:120].decode()))

    # Deconstruct SSE endpoint
    body = {"book_title": "斗破苍穹", "samples": ["第一章 少年萧炎站在斗气大陆..."]}
    req = urllib.request.Request(
        f"{BASE}/projects/init/deconstruct/stream",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        chunk = resp.read(800).decode("utf-8", errors="replace")
        ok = resp.status == 200 and "data:" in chunk
        results.append(("P6-G03 deconstruct/stream", ok, resp.status, chunk[:120]))
    except urllib.error.HTTPError as e:
        results.append(("P6-G03 deconstruct/stream", False, e.code, e.read()[:120].decode()))

    print("\n=== Phase 6 API Acceptance ===")
    passed = failed = 0
    for name, ok, code, detail in results:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"[{status}] {name} | HTTP {code} | {detail}")
    print(f"\nTotal: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

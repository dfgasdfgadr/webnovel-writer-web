"""Phase 2 browser/API acceptance probe."""
import json
import sys
import urllib.parse
import urllib.request

BASE = "http://localhost:8000/api/v1"


def login() -> str:
    data = urllib.parse.urlencode({"username": "admin", "password": "admin123456"}).encode()
    req = urllib.request.Request(
        f"{BASE}/auth/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return json.loads(urllib.request.urlopen(req).read())["access_token"]


def call(method: str, path: str, token: str | None = None, body=None, timeout=60):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read()
        try:
            return resp.status, json.loads(raw)
        except json.JSONDecodeError:
            return resp.status, raw.decode("utf-8", errors="replace")[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:800]


def pick_project(token: str) -> str | None:
    _, projects = call("GET", "/projects", token)
    items = projects.get("items", [])
    # prefer project with chapters
    for p in items:
        _, chs = call("GET", f"/projects/{p['id']}/chapters", token)
        if chs.get("items"):
            return p["id"]
    return items[0]["id"] if items else None


def main():
    token = login()
    results = []

    # LLM settings
    code, llm = call("GET", "/settings/llm", token)
    has_key = bool(llm.get("api_key_masked")) if isinstance(llm, dict) else False
    results.append(("P2-LLM01 GET /settings/llm", code == 200 and has_key, code, llm.get("model") if isinstance(llm, dict) else llm))

    code, test = call("POST", "/settings/llm/test", token, {})
    ok = code == 200 and isinstance(test, dict) and test.get("success") is True
    results.append(("P2-LLM02 POST /settings/llm/test", ok, code, test))

    # MiroFish health (no auth)
    code, sim_health = call("GET", "/simulations/health", None)
    results.append(("P2-F01/P2-NF01 GET /simulations/health", code == 200, code, sim_health))

    pid = pick_project(token)
    if not pid:
        print("No project found")
        return 1

    # Graph
    code, graph = call("GET", f"/agents/graph/{pid}", token)
    nodes = len(graph.get("nodes", [])) if isinstance(graph, dict) else 0
    edges = len(graph.get("edges", [])) if isinstance(graph, dict) else 0
    timeline = len(graph.get("timeline", [])) if isinstance(graph, dict) else 0
    results.append(("P2-F06 GET /agents/graph/{id}", code == 200, code, f"nodes={nodes} edges={edges} timeline={timeline}"))

    # Continuity
    code, cont = call("POST", f"/agents/continuity/{pid}", token, {"chapter_num": 2}, timeout=120)
    results.append(("Continuity POST /agents/continuity/{id}", code == 200, code, str(cont)[:200]))

    # Simulations list
    code, sims = call("GET", f"/simulations?project_id={pid}", token)
    sim_count = len(sims.get("items", [])) if isinstance(sims, dict) else 0
    results.append(("Simulations GET list", code == 200, code, f"count={sim_count}"))

    # PreChapterSim create
    _, chs = call("GET", f"/projects/{pid}/chapters", token)
    ch_list = chs.get("items", [])
    ch_num = ch_list[0]["number"] if ch_list else 1
    code, pre = call(
        "POST",
        "/simulations",
        token,
        {"project_id": pid, "mode": "pre_chapter", "chapter_num": ch_num, "outline": "验收测试章纲"},
        timeout=120,
    )
    pre_ok = code in (200, 201)
    pre_status = pre.get("status") if isinstance(pre, dict) else pre
    results.append(("P2-F02 POST simulations pre_chapter", pre_ok, code, pre_status))

    # BranchExplore
    code, branch = call(
        "POST",
        "/simulations",
        token,
        {"project_id": pid, "mode": "branch_explore", "chapter_num": ch_num, "outline": "分支探索测试"},
        timeout=120,
    )
    branch_ok = code in (200, 201)
    branch_status = branch.get("status") if isinstance(branch, dict) else branch
    results.append(("P2-F04 POST simulations branch_explore", branch_ok, code, branch_status))

    # Search (BM25 persisted)
    q = urllib.parse.quote("主角")
    code, search = call("GET", f"/agents/search/{pid}?q={q}", token)
    results.append(("Phase1-03 BM25 search", code == 200, code, f"hits={len(search) if isinstance(search, list) else search}"))

    print("=== Phase 2 API Acceptance ===")
    fails = 0
    for name, ok, code, detail in results:
        status = "PASS" if ok else "FAIL"
        if not ok:
            fails += 1
        print(f"[{status}] {name} -> HTTP {code} | {detail}")

    return fails


if __name__ == "__main__":
    sys.exit(main())

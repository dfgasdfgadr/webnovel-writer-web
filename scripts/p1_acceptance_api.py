"""Phase 1 pipeline/SSE/API acceptance tests."""
import json
import urllib.parse
import urllib.request
import sys

BASE = "http://localhost:8000/api/v1"
PROJECT_ID = "f75fc9b9-b993-40d5-90e9-7f3b19d337e5"
CHAPTER_ID = "568abaf1-a04e-41ea-87bd-4910b453551b"


def login() -> str:
    data = urllib.parse.urlencode({"username": "admin", "password": "admin123456"}).encode()
    req = urllib.request.Request(
        f"{BASE}/auth/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return json.loads(urllib.request.urlopen(req).read())["access_token"]


def call(method, path, token, body=None):
    headers = {"Authorization": f"Bearer {token}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        raw = resp.read()
        try:
            return resp.status, json.loads(raw)
        except json.JSONDecodeError:
            return resp.status, raw.decode("utf-8", errors="replace")[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:800]


def main():
    token = login()
    tests = []

    # Checkpoint endpoint
    code, cp = call("GET", f"/agents/pipeline/{CHAPTER_ID}/checkpoint", token)
    tests.append(("checkpoint GET", code == 200, code, cp))

    # Reviews GET
    code, rev = call("GET", f"/agents/reviews/{CHAPTER_ID}", token)
    tests.append(("reviews GET", code == 200, code, f"count={len(rev) if isinstance(rev, list) else rev}"))

    # Search endpoint
    code, search = call("GET", f"/agents/search/{PROJECT_ID}?q={urllib.parse.quote('封不觉')}", token)
    tests.append(("search GET", code == 200, code, search if isinstance(search, dict) else str(search)[:200]))

    # Agent runs
    code, runs = call("GET", f"/agents/runs/{PROJECT_ID}", token)
    run_count = len(runs.get("items", [])) if isinstance(runs, dict) else 0
    tests.append(("runs GET", code == 200, code, f"count={run_count}"))

    # Cards/Entities
    code, cards = call("GET", f"/projects/{PROJECT_ID}/cards", token)
    tests.append(("cards GET", code == 200, code, f"count={len(cards.get('items',[])) if isinstance(cards,dict) else cards}"))
    code, entities = call("GET", f"/projects/{PROJECT_ID}/entities", token)
    tests.append(("entities GET", code == 200, code, f"count={len(entities.get('items',[])) if isinstance(entities,dict) else entities}"))
    code, fs = call("GET", f"/projects/{PROJECT_ID}/foreshadowing", token)
    tests.append(("foreshadowing GET", code == 200, code, f"count={len(fs.get('items',[])) if isinstance(fs,dict) else fs}"))

    # Pipeline POST (full flow)
    code, pipe = call(
        "POST",
        f"/agents/pipeline/{CHAPTER_ID}",
        token,
        {"outline": "封不觉第一天到第六面心理诊所实习，主任简单介绍后离开。"},
    )
    tests.append(("pipeline POST", code == 200, code, str(pipe)[:400]))

    # Run review on chapter with content
    code, run_rev = call("POST", f"/agents/reviews/{CHAPTER_ID}/run", token, {})
    tests.append(("review run POST", code in (200, 201), code, str(run_rev)[:300]))

    print("=== Phase 1 API Tests ===")
    for name, ok, code, detail in tests:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name} -> HTTP {code} | {detail}")

    fails = [t for t in tests if not t[1]]
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

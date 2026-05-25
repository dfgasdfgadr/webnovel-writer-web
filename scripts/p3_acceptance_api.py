"""Phase 3 browser/API acceptance probe."""
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


def call(method, path, token, body=None, timeout=120):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
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


def pick_project(token):
    _, projects = call("GET", "/projects", token)
    return projects.get("items", [{}])[0]


def main():
    token = login()
    results = []
    p = pick_project(token)
    pid = p["id"]

    # Polish axes
    code, axes = call("GET", "/agents/polish/axes", token)
    results.append(("P3-F01 polish/axes", code == 200 and isinstance(axes, (list, dict)), code, str(axes)[:120]))

    # Disambiguation list
    code, dis = call("GET", f"/disambiguation/{pid}", token)
    count = len(dis) if isinstance(dis, list) else len(dis.get("items", [])) if isinstance(dis, dict) else 0
    results.append(("P3-DIS01 disambiguation GET", code == 200, code, f"count={count}"))

    # Summaries
    code, sums = call("GET", f"/summaries/{pid}", token)
    sc = len(sums) if isinstance(sums, list) else len(sums.get("items", [])) if isinstance(sums, dict) else 0
    results.append(("P3-SUM01 summaries GET", code == 200, code, f"count={sc}"))

    # Architect synopsis
    code, syn = call("POST", f"/agents/architect/synopsis/{pid}", token, {"premise": "废柴少年逆袭"})
    ok = code == 200 and isinstance(syn, dict) and syn.get("title")
    results.append(("P3-PLAN01 architect/synopsis", ok, code, str(syn)[:150]))

    # Single outline
    code, ol = call("POST", f"/agents/architect/outline/{pid}", token, {"chapter_num": 1, "title": "第一章"})
    results.append(("P3-PLAN02 architect/outline", code == 200, code, str(ol)[:120]))

    # Batch outline (1 chapter only for speed)
    code, batch = call("POST", f"/agents/architect/outline/{pid}/batch", token, {"start_chapter": 1, "end_chapter": 1})
    results.append(("P3-PLAN03 architect/outline/batch", code == 200, code, str(batch)[:120]))

    # Volume plan
    code, vol = call("POST", f"/agents/architect/volume-plan/{pid}", token, {"volume_num": 1})
    results.append(("P3-PLAN04 architect/volume-plan", code == 200, code, str(vol)[:120]))

    # Checkpoint + chapter for metrics
    _, chs = call("GET", f"/projects/{pid}/chapters", token)
    ch_list = chs.get("items", [])
    if ch_list:
        cid = ch_list[0]["id"]
        code, cp = call("GET", f"/agents/pipeline/{cid}/checkpoint", token)
        results.append(("P3-CP01 checkpoint GET", code == 200, code, cp))
        code, metrics = call("GET", f"/agents/reviews/{cid}/metrics", token)
        mc = len(metrics) if isinstance(metrics, list) else 0
        results.append(("P3-F02 review metrics GET", code == 200, code, f"count={mc}"))

    # Simulations adopt endpoint exists
    code, sims = call("GET", f"/simulations?project_id={pid}", token)
    sim_items = sims if isinstance(sims, list) else sims.get("items", []) if isinstance(sims, dict) else []
    if sim_items:
        sid = sim_items[0]["id"]
        code, adopt = call("POST", f"/simulations/{sid}/adopt", token, {"target": "outline"})
        results.append(("P3-SIM01 simulations/adopt", code in (200, 201, 400), code, str(adopt)[:150]))
    else:
        results.append(("P3-SIM01 simulations/adopt", True, 0, "SKIP no sim jobs"))

    print("=== Phase 3 API Probe ===")
    fails = 0
    for name, ok, code, detail in results:
        st = "PASS" if ok else "FAIL"
        if not ok:
            fails += 1
        print(f"[{st}] {name} -> HTTP {code} | {detail}")
    return fails


if __name__ == "__main__":
    sys.exit(main())

"""Phase 1 acceptance API probe."""
import json
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


def req(method: str, path: str, token: str, body=None):
    headers = {"Authorization": f"Bearer {token}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    token = login()
    print("=== LLM Settings ===")
    code, llm = req("GET", "/settings/llm", token)
    print(code, json.dumps(llm, ensure_ascii=False))

    print("\n=== Projects ===")
    code, projects = req("GET", "/projects", token)
    items = projects.get("items", [])
    print(f"{len(items)} projects")
    for p in items[:8]:
        pid = p["id"]
        _, chs = req("GET", f"/projects/{pid}/chapters", token)
        ch_list = chs.get("items", [])
        print(f"  {pid[:8]} | {p['title'][:30]} | {len(ch_list)} chapters")
        if ch_list:
            cid = ch_list[0]["id"]
            _, cp = req("GET", f"/agents/pipeline/{cid}/checkpoint", token)
            _, rev = req("GET", f"/agents/reviews/{cid}", token)
            print(f"    chapter {cid[:8]} checkpoint={cp} reviews={len(rev) if isinstance(rev,list) else rev}")


if __name__ == "__main__":
    main()

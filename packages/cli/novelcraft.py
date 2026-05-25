#!/usr/bin/env python3
"""NovelCraft CLI — command-line interface for AI writing operations.

Usage:
  novelcraft write --project PROJECT_ID --chapter CHAPTER_ID
  novelcraft review --chapter CHAPTER_ID
  novelcraft synopsis --project PROJECT_ID
  novelcraft import --source PATH [--title TITLE]
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error


DEFAULT_API_URL = "http://localhost:8000/api/v1"


def _safe_print(*args, **kwargs):
    """Print with encoding safety for Windows GBK consoles."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode to ASCII with replace for broken consoles
        safe_args = []
        for a in args:
            if isinstance(a, str):
                safe_args.append(a.encode("ascii", errors="replace").decode("ascii"))
            else:
                safe_args.append(a)
        print(*safe_args, **kwargs)


def get_token() -> str:
    """Get JWT token from env or cache file."""
    token = os.environ.get("NOVELCRAFT_TOKEN", "")
    if token:
        return token

    cache_file = os.path.expanduser("~/.novelcraft/token")
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            token = f.read().strip()
            if token:
                return token

    _safe_print("No auth token found. Set NOVELCRAFT_TOKEN env var or login first.", file=sys.stderr)
    sys.exit(1)


def api_request(method: str, path: str, data: dict | None = None, token: str | None = None) -> dict:
    """Make an API request to the NovelCraft backend."""
    url = f"{DEFAULT_API_URL}{path}"
    headers = {"Content-Type": "application/json"}

    token = token or get_token()
    headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 204:
                return {}
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        try:
            error_data = json.loads(error_body)
            _safe_print(f"API Error ({e.code}): {error_data.get('detail', error_body)}", file=sys.stderr)
        except json.JSONDecodeError:
            _safe_print(f"API Error ({e.code}): {error_body}", file=sys.stderr)
        sys.exit(1)


def cmd_login(args):
    """Login and cache token."""
    import getpass

    username = args.username or input("Username: ")
    password = args.password or getpass.getpass("Password: ")

    from urllib.parse import urlencode
    data = urlencode({"username": username, "password": password}).encode()
    req = urllib.request.Request(
        f"{DEFAULT_API_URL}/auth/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            token = result.get("access_token", "")
            if token:
                cache_dir = os.path.expanduser("~/.novelcraft")
                os.makedirs(cache_dir, exist_ok=True)
                with open(os.path.join(cache_dir, "token"), "w") as f:
                    f.write(token)
                _safe_print(f"Logged in successfully. Token cached.")
            else:
                _safe_print("Login failed: no token in response", file=sys.stderr)
                sys.exit(1)
    except urllib.error.HTTPError as e:
        _safe_print(f"Login failed ({e.code})", file=sys.stderr)
        sys.exit(1)


def cmd_write(args):
    """Trigger the writing pipeline for a chapter."""
    token = get_token()

    # Get chapter outline first
    chapter = api_request("GET", f"/projects/{args.project}/chapters/{args.chapter}", token=token)
    outline = chapter.get("outline", "")

    result = api_request("POST", f"/agents/pipeline/{args.chapter}", data={
        "chapter_outline": outline,
    }, token=token)

    if result.get("success"):
        _safe_print(f"Chapter {args.chapter} written successfully.")
        if result.get("blocking_issues"):
            _safe_print(f"Blocking issues: {len(result['blocking_issues'])}")
    else:
        _safe_print(f"Pipeline failed: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)


def cmd_review(args):
    """Get review results for a chapter."""
    issues = api_request("GET", f"/agents/reviews/{args.chapter}")
    _safe_print(f"Review issues: {len(issues)}")
    for issue in issues:
        severity_icon = "[X]" if issue["severity"] == "blocking" else "[!]" if issue["severity"] == "major" else "[-]"
        _safe_print(f"  {severity_icon} [{issue['severity']}] {issue['title']}")
        if issue.get("suggestion"):
            _safe_print(f"     -> {issue['suggestion']}")

    # Also show metrics
    metrics = api_request("GET", f"/agents/reviews/{args.chapter}/metrics")
    if metrics:
        _safe_print("\n7-Dimension Scores:")
        latest = metrics[0]
        dims = [
            ("设定一致性", latest.get("consistency_score", 0)),
            ("时间线", latest.get("timeline_score", 0)),
            ("叙事连贯", latest.get("coherence_score", 0)),
            ("角色OOC", latest.get("ooc_score", 0)),
            ("逻辑因果", latest.get("logic_score", 0)),
            ("伏笔管理", latest.get("foreshadowing_score", 0)),
            ("AI味", latest.get("ai_flavor_score", 0)),
        ]
        for name, score in dims:
            bar = "#" * int(score / 5) + "." * (20 - int(score / 5))
            _safe_print(f"  {name:8s} [{bar}] {score}/100")


def cmd_synopsis(args):
    """Generate a synopsis for a project."""
    result = api_request("POST", f"/agents/architect/synopsis/{args.project}", data={
        "genre": args.genre or "",
        "hook": args.hook or "",
        "protagonist": {},
        "world_building": {},
        "power_system": "",
    })
    _safe_print(f"Synopsis generated: {result.get('title', 'Untitled')}")
    _safe_print(f"Synopsis: {result.get('synopsis', '')[:500]}...")


def cmd_import(args):
    """Import a project from a local directory."""
    _safe_print(f"Scanning: {args.source}")
    scan = api_request("POST", "/projects/import/scan", data={"source_path": args.source})

    if not scan.get("valid"):
        _safe_print(f"Invalid directory: {scan.get('errors', [])}", file=sys.stderr)
        sys.exit(1)

    _safe_print(f"Found: {scan['chapter_count']} chapters, {scan['settings_count']} settings files")
    _safe_print("Importing...")
    result = api_request("POST", "/projects/import", data={
        "source_path": args.source,
        "title": args.title,
    })
    _safe_print(f"Imported: {result['title']} (ID: {result['id']})")


def cmd_list(args):
    """List projects."""
    result = api_request("GET", "/projects")
    _safe_print(f"Projects ({result.get('total', 0)}):")
    for p in result.get("items", []):
        status_icon = "[*]" if p.get("status") == "active" else "[ ]"
        _safe_print(f"  {status_icon} {p['id'][:8]}.. {p['title']} ({p.get('genre', 'N/A')})")


def main():
    parser = argparse.ArgumentParser(description="NovelCraft CLI — AI web-novel writing platform")
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # login
    p_login = sub.add_parser("login", help="Login and cache auth token")
    p_login.add_argument("--username", "-u", help="Username")
    p_login.add_argument("--password", "-p", help="Password")

    # write
    p_write = sub.add_parser("write", help="Run writing pipeline")
    p_write.add_argument("--project", "-P", required=True, help="Project ID")
    p_write.add_argument("--chapter", "-C", required=True, help="Chapter ID")

    # review
    p_review = sub.add_parser("review", help="Get review results")
    p_review.add_argument("--chapter", "-C", required=True, help="Chapter ID")

    # synopsis
    p_synopsis = sub.add_parser("synopsis", help="Generate synopsis")
    p_synopsis.add_argument("--project", "-P", required=True, help="Project ID")
    p_synopsis.add_argument("--genre", help="Genre")
    p_synopsis.add_argument("--hook", help="Core hook")

    # import
    p_import = sub.add_parser("import", help="Import project from directory")
    p_import.add_argument("--source", "-S", required=True, help="Source directory path")
    p_import.add_argument("--title", "-T", help="Project title")

    # list
    sub.add_parser("list", help="List projects")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "login": cmd_login,
        "write": cmd_write,
        "review": cmd_review,
        "synopsis": cmd_synopsis,
        "import": cmd_import,
        "list": cmd_list,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

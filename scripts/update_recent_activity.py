from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

START = "<!-- RECENT_ACTIVITY:start -->"
END = "<!-- RECENT_ACTIVITY:end -->"

username = os.environ["GITHUB_USERNAME"]
token = os.environ["GH_TOKEN"]

request = Request(
    f"https://api.github.com/users/{username}/events/public?per_page=30",
    headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": f"{username}-profile-readme",
        "X-GitHub-Api-Version": "2022-11-28",
    },
)

with urlopen(request, timeout=20) as response:
    events = json.load(response)


def repo_link(repo: str) -> str:
    return f"[{repo}](https://github.com/{repo})"


def event_line(event: dict) -> str | None:
    event_type = event.get("type", "")
    repo = event.get("repo", {}).get("name", "")
    if not repo or repo == f"{username}/{username}":
        return None

    payload = event.get("payload", {})
    created_at = event.get("created_at", "")
    try:
        date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        date = created_at[:10] or "recently"

    if event_type == "PushEvent":
        count = len(payload.get("commits") or [])
        noun = "commit" if count == 1 else "commits"
        return f"- `{date}` Pushed {count} {noun} to {repo_link(repo)}"

    if event_type == "CreateEvent":
        ref_type = payload.get("ref_type")
        ref = payload.get("ref")
        if ref_type == "repository":
            return f"- `{date}` Created {repo_link(repo)}"
        if ref_type and ref:
            return f"- `{date}` Created {ref_type} `{ref}` in {repo_link(repo)}"

    if event_type == "PullRequestEvent":
        action = payload.get("action", "updated")
        pr = payload.get("pull_request") or {}
        number = pr.get("number")
        title = (pr.get("title") or "").strip()
        url = pr.get("html_url")
        merged = pr.get("merged")
        verb = "Merged" if merged else action.capitalize()
        if number and url:
            label = f"#{number}" + (f" {title}" if title else "")
            return f"- `{date}` {verb} [{label}]({url}) in {repo_link(repo)}"

    if event_type == "IssuesEvent":
        action = payload.get("action", "updated").capitalize()
        issue = payload.get("issue") or {}
        number = issue.get("number")
        title = (issue.get("title") or "").strip()
        url = issue.get("html_url")
        if number and url:
            label = f"#{number}" + (f" {title}" if title else "")
            return f"- `{date}` {action} issue [{label}]({url}) in {repo_link(repo)}"

    if event_type == "ReleaseEvent":
        release = payload.get("release") or {}
        tag = release.get("tag_name") or "release"
        url = release.get("html_url")
        if url:
            return f"- `{date}` Published release [`{tag}`]({url}) in {repo_link(repo)}"

    if event_type == "ForkEvent":
        return f"- `{date}` Forked {repo_link(repo)}"

    if event_type == "WatchEvent":
        return f"- `{date}` Starred {repo_link(repo)}"

    return None


lines: list[str] = []
for event in events:
    line = event_line(event)
    if line:
        lines.append(line)
    if len(lines) == 5:
        break

if not lines:
    lines = ["_No recent public activity yet._"]

readme_path = Path("README.md")
readme = readme_path.read_text(encoding="utf-8")

if START not in readme or END not in readme:
    raise RuntimeError("Recent activity markers are missing from README.md")

before, rest = readme.split(START, 1)
_, after = rest.split(END, 1)
updated = f"{before}{START}\n" + "\n".join(lines) + f"\n{END}{after}"

if updated != readme:
    readme_path.write_text(updated, encoding="utf-8")

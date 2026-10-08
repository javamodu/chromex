"""GitHub araştırma worker'ı.

Birincil yol `gh` CLI'dir (kimlik doğrulamayı kendi yönetir); kurulu değilse
REST API'ye düşer (GITHUB_TOKEN opsiyonel, rate limit için önerilir).
Tüm işlemler READ seviyesindedir ve audit'e yazılır.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from core import store
from policygate import ActionRequest, audit, require, secrets
from core.http import request_json

WORKER = "github"
API = "https://api.github.com"


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _rest_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = secrets.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def search_repos(query: str, limit: int = 10) -> list[dict]:
    audit.log_event("github_search", WORKER, "READ", "auto",
                    {"query": query, "limit": limit})
    if _gh_available():
        out = subprocess.run(
            ["gh", "search", "repos", query, "--limit", str(limit),
             "--json", "fullName,description,stargazersCount,url"],
            capture_output=True, text=True, check=True,
        ).stdout
        items = json.loads(out or "[]")
    else:
        data = request_json(
            "GET", f"{API}/search/repositories", WORKER,
            headers=_rest_headers(),
            params={"q": query, "per_page": limit, "sort": "stars"},
        )
        items = [
            {
                "fullName": r["full_name"],
                "description": r.get("description"),
                "stargazersCount": r.get("stargazers_count"),
                "url": r.get("html_url"),
            }
            for r in data.get("items", [])
        ]
    for item in items:
        store.save("github", "repo", item.get("url"), item.get("fullName"),
                   json.dumps(item, ensure_ascii=False))
    return items


def repo_issues(repo: str, state: str = "open", limit: int = 20) -> list[dict]:
    audit.log_event("github_issues", WORKER, "READ", "auto",
                    {"repo": repo, "state": state, "limit": limit})
    data = request_json(
        "GET", f"{API}/repos/{repo}/issues", WORKER,
        headers=_rest_headers(),
        params={"state": state, "per_page": limit},
    )
    issues = [
        {"number": i["number"], "title": i["title"],
         "url": i["html_url"], "state": i["state"]}
        for i in data
        if "pull_request" not in i  # PR'ları ayıkla
    ]
    for issue in issues:
        store.save("github", "issue", issue["url"],
                   f"{repo}#{issue['number']} {issue['title']}", None)
    return issues

def create_pr(title: str, body: str = "", base: str = "main",
              head: str | None = None, draft: bool = False) -> str:
    """gh ile pull request açar — MODIFY seviyesi, kullanıcı onayı ister."""
    if not _gh_available():
        raise RuntimeError(
            "gh CLI gerekli (winget install GitHub.cli; sonra: gh auth login).")
    if head is None:
        try:
            head = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True).stdout.strip()
        except FileNotFoundError:
            head = ""
    require(ActionRequest(
        worker=WORKER, action="github.create_pr", level="MODIFY",
        summary="GitHub'da pull request AÇILACAK.",
        details={
            "title": title,
            "base": base,
            "head": head or "(gh mevcut dalı kullanacak)",
            "draft": draft,
            "body_önizleme": body[:200],
        },
    ))
    cmd = ["gh", "pr", "create", "--title", title, "--body", body,
           "--base", base]
    if head:
        cmd += ["--head", head]
    if draft:
        cmd.append("--draft")
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout).strip()[:500])
    url = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else ""
    audit.log_event("github_pr_created", WORKER, "MODIFY", "done",
                    {"url": url, "title": title, "base": base, "head": head})
    store.save("github", "pr", url, title, None)
    return url

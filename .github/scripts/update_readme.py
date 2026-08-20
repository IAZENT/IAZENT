"""
Fetches public repos for GITHUB_USERNAME, sorts by last pushed,
takes top 6 (excluding the profile repo itself), and rewrites
the Projects section in README.md between marker comments.
"""

import os
import re
import requests

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

# Repos to always exclude
EXCLUDE = {USERNAME.lower(), "iazent"}  # profile repo

def fetch_repos():
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "sort": "pushed", "type": "public"},
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def build_table(repos):
    # Filter, sort by pushed_at desc, take top 6
    filtered = [
        r for r in repos
        if r["name"].lower() not in EXCLUDE and not r["fork"]
    ]
    filtered.sort(key=lambda r: r["pushed_at"], reverse=True)
    top = filtered[:6]

    rows = []
    for r in top:
        name = r["name"]
        url = r["html_url"]
        desc = (r["description"] or "").replace("|", "\\|").replace("--", "-")
        # strip em dashes just in case
        desc = desc.replace("\u2014", "-").replace("\u2013", "-")
        lang = r.get("language") or ""
        lang_badge = f"`{lang}`" if lang else ""
        rows.append(f"| [**{name}**]({url}) | {desc} | {lang_badge} |")

    header = (
        "| Repo | Description | Lang |\n"
        "|:----:|:------------|:----:|"
    )
    return header + "\n" + "\n".join(rows)

def update_readme(table: str):
    start_marker = "<!-- PROJECTS:START -->"
    end_marker = "<!-- PROJECTS:END -->"

    with open("README.md", "r") as f:
        content = f.read()

    new_block = f"{start_marker}\n{table}\n{end_marker}"

    if start_marker in content:
        # Replace existing block
        content = re.sub(
            rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
            new_block,
            content,
            flags=re.DOTALL,
        )
    else:
        print("Markers not found in README.md -- nothing updated.")
        return

    with open("README.md", "w") as f:
        f.write(content)

    print("README.md updated.")

if __name__ == "__main__":
    repos = fetch_repos()
    table = build_table(repos)
    update_readme(table)

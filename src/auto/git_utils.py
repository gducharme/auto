from __future__ import annotations

"""Git repository maintenance helpers."""

import subprocess
from typing import List



def _run_git(cmd: List[str]) -> subprocess.CompletedProcess:
    """Run a git command and return the completed process."""
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def cleanup_merged_branches(remote: str = "origin", main: str = "main") -> None:
    """Remove branches merged into ``main`` locally and on ``remote``."""
    subprocess.run(["git", "fetch", "--prune", remote], check=True)
    subprocess.run(["git", "checkout", main], check=True)
    subprocess.run(["git", "pull", remote, main], check=True)

    local = _run_git(["git", "branch", "--merged"]).stdout.splitlines()
    to_delete = []
    for line in local:
        branch = line.replace("*", "").strip()
        if branch and branch not in (main, "develop"):
            to_delete.append(branch)

    for br in to_delete:
        subprocess.run(["git", "branch", "-d", br], check=True)

    merged = _run_git(["git", "branch", "-r", "--merged", f"{remote}/{main}"]).stdout.splitlines()
    prefix = f"{remote}/"
    remote_delete = []
    for line in merged:
        line = line.strip()
        if not line.startswith(prefix):
            continue
        br = line[len(prefix):]
        if br not in (main, "develop", "HEAD"):
            remote_delete.append(br)

    for br in remote_delete:
        subprocess.run(["git", "push", remote, "--delete", br], check=True)


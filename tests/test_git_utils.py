from auto.git_utils import cleanup_merged_branches
import subprocess


def test_cleanup_branches(monkeypatch):
    calls = []

    def fake_run(cmd, capture_output=False, text=False, check=False):
        calls.append(cmd)
        from subprocess import CompletedProcess
        if cmd[:3] == ["git", "branch", "--merged"]:
            return CompletedProcess(cmd, 0, stdout="  main\n  feature\n")
        if cmd[:4] == ["git", "branch", "-r", "--merged"]:
            return CompletedProcess(
                cmd,
                0,
                stdout="  origin/main\n  origin/HEAD -> origin/main\n  origin/old\n",
            )
        return CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    cleanup_merged_branches()

    assert ["git", "branch", "-d", "feature"] in calls
    assert ["git", "push", "origin", "--delete", "old"] in calls

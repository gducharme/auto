from pathlib import Path

import pytest

from auto.code_synthesizer import CodeSynthesizer


@pytest.fixture
def sample_repo(tmp_path):
    (tmp_path / "CONTEXT.md").write_text("context")
    src = tmp_path / "src" / "auto"
    src.mkdir(parents=True)
    (src / "a.py").write_text("a = 1")
    (src / "b.py").write_text("b = 2")
    mig = tmp_path / "alembic" / "versions"
    mig.mkdir(parents=True)
    (mig / "m.py").write_text("m = 3")
    return tmp_path


def test_synthesize_uses_env_variable(sample_repo, monkeypatch):
    def fake_collect(self, base: Path, limit: int):
        return [base / "dummy.py"] * limit

    monkeypatch.setattr(CodeSynthesizer, "_collect_files", fake_collect)
    cs = CodeSynthesizer(sample_repo)

    monkeypatch.setenv("CODE_SYNTH_FILE_LIMIT", "1")
    result1 = cs.synthesize({})
    assert len(result1) == 2

    monkeypatch.setenv("CODE_SYNTH_FILE_LIMIT", "3")
    result2 = cs.synthesize({})
    assert len(result2) == 6


def test_synthesize_reads_context(sample_repo, monkeypatch):
    captured = {"configured": False, "read": 0}

    def fake_configure():
        captured["configured"] = True

    def fake_read_text(self, encoding="utf-8"):
        if self.name == "CONTEXT.md":
            captured["read"] += 1
        return "context"

    monkeypatch.setattr("auto.code_synthesizer.configure_logging", fake_configure)
    monkeypatch.setattr(Path, "read_text", fake_read_text)

    cs = CodeSynthesizer(sample_repo)
    cs.synthesize({})

    assert captured["configured"]
    assert captured["read"] == 1

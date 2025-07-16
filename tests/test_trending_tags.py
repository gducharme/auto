import sys
from pathlib import Path
from invoke import Context

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import tasks  # noqa: E402
import mastodon  # noqa: E402


def test_trending_tags_outputs(monkeypatch, capsys):
    class DummyMastodon:
        def trending_tags(self, limit=None):
            return [{"name": "python"}, {"name": "coding"}]

    monkeypatch.setattr(mastodon, "Mastodon", lambda **_: DummyMastodon())

    tasks.trending_tags(Context(), limit=2)

    captured = capsys.readouterr()
    assert "python" in captured.out
    assert "coding" in captured.out

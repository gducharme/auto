import pytest
from invoke import Context

import tasks as inv


class DummyContext(Context):
    """Collect commands passed to ``run`` without executing them."""

    def __init__(self):
        super().__init__()
        self.commands = []

    def run(self, cmd, *_, pty=False, **__):  # type: ignore[override]
        self.commands.append((cmd, pty))


TEST_CASES = [
    (inv.install_deps, [], {}, "pip install -r requirements.txt"),
    (
        inv.uv,
        [],
        {},
        "python -m auto.cli maintenance uv --host 127.0.0.1 --port 8000 --reload",
    ),
    (inv.scheduler, [], {}, "python -m auto.scheduler"),
    (inv.ingest, [], {}, "python -m auto.cli maintenance ingest"),
    (inv.list_previews, [], {}, "python -m auto.cli publish list-previews"),
    (
        inv.list_substacks,
        [],
        {"published": True, "unpublished": True},
        "python -m auto.cli publish list-substacks -p -u",
    ),
    (inv.list_schedule, [], {}, "python -m auto.cli publish list-schedule"),
    (
        inv.generate_preview,
        [123],
        {},
        "python -m auto.cli publish generate-preview --post-id 123 --network mastodon",
    ),
    (
        inv.create_preview,
        [123],
        {"when": "now", "dry_run": True},
        "python -m auto.cli publish create-preview --post-id 123 --network mastodon --when now --dry-run",
    ),
    (
        inv.edit_preview,
        [123],
        {"network": "twitter"},
        "python -m auto.cli publish edit-preview --post-id 123 --network twitter",
    ),
    (
        inv.trending_tags,
        [],
        {"limit": 3, "instance": "mastodon.social", "token": "tok"},
        "python -m auto.cli publish trending-tags --limit 3 --instance mastodon.social --token tok",
    ),
    (inv.sync_mastodon_posts, [], {}, "python -m auto.cli publish sync-mastodon-posts"),
    (
        inv.update_deps,
        [],
        {"freeze": True},
        "python -m auto.cli maintenance update-deps --freeze",
    ),
    (
        inv.cleanup_branches,
        [],
        {"remote": "up", "main": "dev"},
        "python -m auto.cli maintenance cleanup-branches --remote up --main dev",
    ),
    (
        inv.metrics,
        [],
        {"host": "0.0.0.0", "port": 9000},
        "python -m auto.cli maintenance metrics --host 0.0.0.0 --port 9000",
    ),
    (inv.safari_control, [], {}, "python -m auto.cli automation control-safari"),
    (
        inv.replay,
        [],
        {"name": "facebook"},
        "python -m auto.cli automation replay facebook",
    ),
    (
        inv.parse_plan,
        [],
        {},
        "python -c 'from auto.plan.parser import parse_plan; parse_plan(\"PLAN.md\")'",
    ),
    (
        inv.execute_plan,
        [],
        {"plan": "plan.json"},
        "python -m auto.automation.plan_executor plan.json",
    ),
    (inv.install_hooks, [], {}, "pre-commit install"),
    (inv.tests, [], {"marker": "unit"}, "pytest -m unit"),
    (inv.help, [], {}, "invoke --list"),
]


@pytest.mark.parametrize("func,args,kwargs,expected", TEST_CASES)
def test_invoke_tasks(func, args, kwargs, expected):
    ctx = DummyContext()
    func(ctx, *args, **kwargs)
    assert ctx.commands == [(expected, True)]

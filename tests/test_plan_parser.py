import textwrap
from auto.plan.parser import parse_plan


def test_parse_plan_basic(tmp_path):
    sample = textwrap.dedent(
        """
        # Roadmap

        ## Setup
        - Install dependencies
        - Run tests

        ## Deploy
        1. Build image
        2. Push to registry
        """
    )
    plan = tmp_path / "plan.md"
    plan.write_text(sample)

    tasks = parse_plan(plan, out_dir=tmp_path)

    assert [t.id for t in tasks] == ["1", "2", "3", "4"]
    assert [t.heading for t in tasks] == [
        "Roadmap / Setup",
        "Roadmap / Setup",
        "Roadmap / Deploy",
        "Roadmap / Deploy",
    ]
    assert [t.text for t in tasks] == [
        "Install dependencies",
        "Run tests",
        "Build image",
        "Push to registry",
    ]

from auto.cli.helpers import _get_medium_magic_link


def test_get_medium_magic_link(monkeypatch):
    sample = (
        "If the button above doesn\u2019t work, paste this link into your web browser:\n"
        "https://medium.com/m/callback/email?token=d4a805f6a804&operation=login&state=medium\n"
    )

    def fake_run(*args, **kwargs):
        from subprocess import CompletedProcess

        return CompletedProcess(args, 0, stdout=sample, stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    link = _get_medium_magic_link()
    assert (
        link
        == "https://medium.com/m/callback/email?token=d4a805f6a804&operation=login&state=medium"
    )

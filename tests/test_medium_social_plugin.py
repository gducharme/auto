from auto.socials.medium_client import MediumClient
from tests.test_medium_client import DummyController
import asyncio


def test_medium_plugin_post(monkeypatch):
    monkeypatch.setenv("MEDIUM_EMAIL", "user@example.com")
    monkeypatch.setenv("MEDIUM_PASSWORD", "secret")
    controller = DummyController()
    plugin = MediumClient(safari=controller)
    asyncio.run(plugin.post("hello"))
    assert ("open", "https://medium.com/m/signin") in controller.calls
    assert ("open", "https://medium.com/new-story") in controller.calls
    assert ("fill", "input[name='email']", "user@example.com") in controller.calls
    assert ("fill", "input[name='password']", "secret") in controller.calls
    assert ("fill", "body", "hello") in controller.calls

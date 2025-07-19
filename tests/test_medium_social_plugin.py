from auto.socials.medium_client import MediumClient
from tests.test_medium_client import DummyDriver
import asyncio


def test_medium_plugin_post(monkeypatch):
    monkeypatch.setenv("MEDIUM_EMAIL", "user@example.com")
    monkeypatch.setenv("MEDIUM_PASSWORD", "secret")
    driver = DummyDriver()
    plugin = MediumClient(driver=driver)
    asyncio.run(plugin.post("hello"))
    assert ("get", "https://medium.com/m/signin") in driver.calls
    assert ("get", "https://medium.com/new-story") in driver.calls
    assert ("send_keys", "email", "user@example.com") in driver.calls
    assert ("send_keys", "password", "secret") in driver.calls
    assert ("send_keys", "body", "hello") in driver.calls

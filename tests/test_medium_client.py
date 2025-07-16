from auto.automation.medium import MediumClient


class DummyElement:
    def __init__(self, calls, value):
        self.calls = calls
        self.value = value

    def send_keys(self, keys):
        self.calls.append(("send_keys", self.value, keys))

    def click(self):
        self.calls.append(("click", self.value))


class DummyDriver:
    def __init__(self):
        self.calls = []

    def get(self, url):
        self.calls.append(("get", url))

    def find_element(self, by, value):
        self.calls.append(("find", by, value))
        return DummyElement(self.calls, value)

    def quit(self):
        self.calls.append(("quit",))


def test_login_uses_env(monkeypatch):
    monkeypatch.setenv("MEDIUM_EMAIL", "user@example.com")
    monkeypatch.setenv("MEDIUM_PASSWORD", "secret")
    driver = DummyDriver()
    client = MediumClient(driver=driver)
    client.login()
    assert ("get", "https://medium.com/m/signin") in driver.calls
    assert ("send_keys", "email", "user@example.com") in driver.calls
    assert ("send_keys", "password", "secret") in driver.calls

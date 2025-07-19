from auto.automation.medium import MediumClient


class DummyController:
    def __init__(self):
        self.calls = []

    def open(self, url):
        self.calls.append(("open", url))

    def fill(self, selector, text):
        self.calls.append(("fill", selector, text))

    def click(self, selector):
        self.calls.append(("click", selector))

    def run_js(self, code):
        self.calls.append(("js", code))
        return ""

    def close_tab(self):
        self.calls.append(("close_tab",))


def test_login_uses_env(monkeypatch):
    monkeypatch.setenv("MEDIUM_EMAIL", "user@example.com")
    monkeypatch.setenv("MEDIUM_PASSWORD", "secret")
    controller = DummyController()
    client = MediumClient(safari=controller)
    client.login()
    assert ("open", "https://medium.com/m/signin") in controller.calls
    assert ("fill", "input[name='email']", "user@example.com") in controller.calls
    assert ("fill", "input[name='password']", "secret") in controller.calls

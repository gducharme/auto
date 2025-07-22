import types
import sys
from auto.cli.automation import query_llm

class DummyLM:
    def __call__(self, *args, **kwargs):
        return ["pong"]

def test_query_llm_handles_list(monkeypatch):
    dummy = types.ModuleType('dspy')
    dummy.LM = lambda *args, **kwargs: DummyLM()
    dummy.configure = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, 'dspy', dummy)
    assert query_llm("ping") == "pong"

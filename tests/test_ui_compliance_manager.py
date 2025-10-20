import builtins
import sys
import os
import pytest

# Ensure repository root is on sys.path so tests can import `src.workshop` modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.workshop import ui_compliance_manager as ui_mod


class MockCMRefine:
    CATEGORY_MAP = {
        "Data protection & Privacy": {
            "scope": "GDPR",
            "description": "Scope: GDPR",
        }
    }

    def __init__(self):
        self.search_called = False

    def search_updates(self, topic):
        # Initial call indicates need for refinement
        self.search_called = True
        return {"status": "completed", "message_text": "", "citations": [], "note": "No authoritative citations found; please refine."}

    def handle_query(self, query):
        # Return a substantive refined answer with citations
        return {"status": "completed", "message_text": "Refined result with sources.", "citations": [{"url": "https://example.org/gdpr"}], "note": None}


class MockCMGood:
    CATEGORY_MAP = {
        "Data protection & Privacy": {
            "scope": "GDPR",
            "description": "Scope: GDPR",
        }
    }

    def search_updates(self, topic):
        return {"status": "completed", "message_text": "Found authoritative sources.", "citations": [{"url": "https://example.org/gdpr"}], "note": None}


def make_input_responder(responses):
    responses = list(responses)

    def responder(prompt=''):
        if not responses:
            raise EOFError("No more input")
        return responses.pop(0)

    return responder


def test_refine_confirm_flow(monkeypatch, capsys):
    # Force non-rich fallback
    monkeypatch.setattr(ui_mod, 'RICH_AVAILABLE', False)
    mock_cm = MockCMRefine()
    ui = ui_mod.UIComplianceManager(cm=mock_cm)

    # Simulate: select category 1, provide refinement 'EU', confirm 'y', then exit '0'
    inputs = ['1', 'EU', 'y', '0']
    monkeypatch.setattr(builtins, 'input', make_input_responder(inputs))

    ui.run()

    # Confirm that refinement was called and user confirmed the result
    assert ui.confirmed is True


def test_no_refinement_needed(monkeypatch, capsys):
    monkeypatch.setattr(ui_mod, 'RICH_AVAILABLE', False)
    mock_cm = MockCMGood()
    ui = ui_mod.UIComplianceManager(cm=mock_cm)

    # Simulate: select category 1, then exit 0
    inputs = ['1', '0']
    monkeypatch.setattr(builtins, 'input', make_input_responder(inputs))

    ui.run()

    # Since the result had citations, we did not go through refinement loop; confirmed remains False
    assert ui.confirmed is False

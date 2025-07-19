import os
import pytest

from auto.automation.safari import SafariController
from auto.automation.medium import MediumClient  # noqa: E402


@pytest.mark.integration
def test_medium_login_real():
    """Verify that Medium login succeeds with real credentials."""
    email = os.getenv("MEDIUM_EMAIL")
    password = os.getenv("MEDIUM_PASSWORD")
    if not email or not password:
        pytest.skip("MEDIUM_EMAIL and MEDIUM_PASSWORD must be set")

    controller = SafariController()
    client = MediumClient(safari=controller)
    try:
        client.login()
    finally:
        client.close()

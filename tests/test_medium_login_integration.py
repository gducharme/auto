import os
import pytest
from selenium import webdriver
from auto.automation.medium import MediumClient  # noqa: E402


@pytest.mark.integration
def test_medium_login_real():
    """Verify that Medium login succeeds with real credentials."""
    email = os.getenv("MEDIUM_EMAIL")
    password = os.getenv("MEDIUM_PASSWORD")
    if not email or not password:
        pytest.skip("MEDIUM_EMAIL and MEDIUM_PASSWORD must be set")

    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)

    client = MediumClient(driver=driver)
    try:
        client.login()
    finally:
        client.close()

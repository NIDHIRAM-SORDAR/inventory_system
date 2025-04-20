import os
import time
from pathlib import Path

import pytest
import requests
from playwright.sync_api import sync_playwright
from reflex.testing import AppHarness


def get_wsl_host():
    """Get the appropriate host IP for the environment (WSL, Linux, or others)."""
    # Allow override via environment variable for flexibility
    if os.environ.get("TEST_HOST"):
        return os.environ.get("TEST_HOST")

    # Detect WSL environment
    is_wsl = False
    try:
        with open("/proc/version", "r") as f:
            if "microsoft" in f.read().lower():
                is_wsl = True
    except FileNotFoundError:
        pass

    if is_wsl:
        # WSL: Try to get the host IP from /etc/resolv.conf
        try:
            with open("/etc/resolv.conf") as f:
                for line in f:
                    if "nameserver" in line:
                        return line.strip().split()[1]
        except Exception:
            return "localhost"
    else:
        # Non-WSL Linux, Windows, or Mac: Use localhost or system-specific logic
        return "localhost"

    return "localhost"


@pytest.fixture(scope="session")
def inventory_app():
    """Start the inventory app using AppHarness."""
    with AppHarness.create(
        root=Path(__file__).parent.parent.parent, app_name="inventory_system"
    ) as harness:
        assert harness.frontend_url, "Frontend URL unavailable"
        wsl_host = get_wsl_host()
        frontend_urls = [
            harness.frontend_url,
            harness.frontend_url.replace("localhost", "127.0.0.1"),
            harness.frontend_url.replace("localhost", wsl_host),
        ]
        print(f"Starting app, trying URLs: {frontend_urls}")
        start_time = time.time()
        timeout = 90
        responsive_url = None
        for url in frontend_urls:
            print(f"Testing {url}/login")
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(
                        f"{url}/login", timeout=5, allow_redirects=True
                    )
                    print(f"Response status: {response.status_code} for {url}/login")
                    if response.status_code == 200:
                        print(f"Frontend responsive at {url}")
                        responsive_url = url
                        break
                except requests.RequestException as e:
                    print(
                        f"Waiting for frontend... ({time.time() - start_time:.1f}s, error: {e})"  # noqa: E501
                    )
                time.sleep(1)
            if responsive_url:
                break
        else:
            raise RuntimeError(f"Frontend did not respond within {timeout}s")
        if responsive_url != harness.frontend_url:
            harness.frontend_url = responsive_url
        yield harness


@pytest.fixture
def edge_page():
    """Provide a Playwright page running in Microsoft Edge."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(20000)
        page.set_default_navigation_timeout(25000)
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        yield page
        context.close()
        browser.close()

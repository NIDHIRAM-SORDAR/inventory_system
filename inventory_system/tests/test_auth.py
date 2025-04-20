import re
import time
from pathlib import Path

import pytest
import reflex as rx
import reflex_local_auth
import requests
from playwright.sync_api import Page, expect, sync_playwright
from reflex.testing import AppHarness
from sqlmodel import select

from inventory_system.models.user import Supplier, UserInfo

# Test user constants
TEST_USERNAME = "test_user"
TEST_PASSWORD = "Test@1234"  # Meets password requirements
TEST_EMAIL = "test@example.com"
TEST_ID = "12345"


def get_wsl_host():
    """Get WSL2 host IP if running in WSL."""
    try:
        with open("/etc/resolv.conf") as f:
            for line in f:
                if "nameserver" in line:
                    return line.strip().split()[1]
    except Exception:
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


@pytest.fixture(scope="session")
def test_users_cleaned_up():
    """Clean up test users, their UserInfo, and Supplier records before tests."""
    with rx.session() as session:
        for username in [TEST_USERNAME]:
            test_user = session.exec(
                select(reflex_local_auth.LocalUser).where(
                    reflex_local_auth.LocalUser.username == username
                )
            ).one_or_none()
            if test_user:
                user_info = session.exec(
                    select(UserInfo).where(UserInfo.user_id == test_user.id)
                ).all()
                for info in user_info:
                    supplier = session.exec(
                        select(Supplier).where(Supplier.user_info_id == info.id)
                    ).all()
                    for supp in supplier:
                        session.delete(supp)
                    session.delete(info)
                session.delete(test_user)
        session.commit()


@pytest.fixture
def edge_page():
    """Provide a Playwright page running in Microsoft Edge."""
    with sync_playwright() as playwright:
        # Launch Microsoft Edge (stable channel)
        browser = playwright.chromium.launch(channel="msedge", headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Set timeouts
        page.set_default_timeout(20000)  # 10s for actions
        page.set_default_navigation_timeout(25000)  # 15s for navigation

        # Log console messages for debugging
        page.on("console", lambda msg: print(f"Console: {msg.text}"))

        yield page
        context.close()
        browser.close()


@pytest.mark.usefixtures("test_users_cleaned_up")
def test_logout_flow(inventory_app: AppHarness, edge_page: Page):
    """Test the logout flow of the inventory app in Microsoft Edge."""
    assert inventory_app.frontend_url, "Frontend URL missing"

    def _url(url):
        """Create a regex URL pattern."""
        return re.compile(inventory_app.frontend_url + url)

    page = edge_page

    # Navigate to login page with retry
    for attempt in range(1, 4):
        try:
            print(f"Navigating to login page (attempt {attempt}/3)")
            page.goto(inventory_app.frontend_url + "/login")
            page.wait_for_load_state("networkidle")
            expect(page).to_have_url(_url("/login/"))
            break
        except Exception as e:
            print(f"Navigation failed: {e}")
            if attempt == 3:
                raise
            time.sleep(2)

    # Register a test user
    page.get_by_role("link", name="Don't have an account").click()
    expect(page).to_have_url(_url("/register/"), timeout=20000)
    page.get_by_placeholder("Enter your ID").fill(TEST_ID)
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your email").fill(TEST_EMAIL)
    page.get_by_placeholder("Enter your password").fill(TEST_PASSWORD)
    page.get_by_placeholder("Confirm your password").fill(TEST_PASSWORD)
    signup_button = page.get_by_role("button", name="Sign Up", exact=True)
    expect(signup_button).to_be_enabled(timeout=15000)
    signup_button.click()
    expect(page).to_have_url(_url("/login/"), timeout=20000)

    # Log in as the test user
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your password").fill(TEST_PASSWORD)
    login_button = page.get_by_role("button", name="Login", exact=True)
    expect(login_button).to_be_enabled(timeout=15000)
    login_button.click()
    expect(page).to_have_url(_url("/overview/"), timeout=30000)

    # Verify logged-in state
    expect(page.get_by_text(TEST_USERNAME)).to_be_visible(timeout=15000)

    # Open the user dropdown
    navbar = page.get_by_role("navigation")
    dropdown_trigger = navbar.get_by_test_id("user-avatar")
    expect(dropdown_trigger).to_be_visible(timeout=15000)
    dropdown_trigger.click()

    # Select the logout menu item
    logout_button = page.get_by_role("menuitem").filter(has=page.get_by_text("Logout"))
    expect(logout_button).to_be_visible(timeout=15000)
    logout_button.click()

    # Wait for the logout dialog
    dialog_locator = page.locator(
        '[role="alertdialog"][data-state="open"]:has-text("Log Out")'
    ).nth(1)
    dialog_locator.wait_for(state="visible", timeout=20000)

    expect(dialog_locator).to_contain_text(
        "Are you sure you want to log out?", timeout=15000
    )

    # Click the Confirm button
    confirm_button = dialog_locator.locator('button:has-text("Confirm")').first
    expect(confirm_button).to_be_visible(timeout=3000)
    confirm_button.click(timeout=50000)

    # Wait for the dialog to close
    expect(dialog_locator).to_be_hidden(timeout=30000)

    # Verify navigation to homepage
    page.wait_for_url(_url("/"), timeout=50000)
    expect(page).to_have_url(_url("/"), timeout=50000)
    expect(page).to_have_title("Telecom Inventory System", timeout=30000)

    # Verify logged-out state
    expect(page.get_by_role("button", name="Get Started")).to_be_visible(timeout=30000)

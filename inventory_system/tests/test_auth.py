from __future__ import annotations

import re
import time
from pathlib import Path

import pytest
import reflex as rx
import requests
from playwright.sync_api import Page, expect
from reflex.testing import AppHarness
from sqlmodel import select

from inventory_system.models.user import LocalUser, Supplier, UserInfo

# Test user constants
TEST_USERNAME = "test_user"
TEST_PASSWORD = "Test@1234"  # Meets password requirements
TEST_EMAIL = "test@example.com"
TEST_ID = "12345"
ADMIN_USERNAME = "admin_user"
ADMIN_PASSWORD = "Admin@1234"
ADMIN_EMAIL = "admin@example.com"
ADMIN_ID = "67890"


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
                        print(
                            f"Frontend responsive at {url} (status: {response.status_code})"  # noqa: E501
                        )
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
        for username in [TEST_USERNAME, "admin_user"]:
            test_user = session.exec(
                select(LocalUser).where(LocalUser.username == username)
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


@pytest.mark.usefixtures("test_users_cleaned_up")
def test_auth_flow(inventory_app: AppHarness, page: Page):
    """Test the authentication flow of the inventory app."""
    assert inventory_app.frontend_url, "Frontend URL missing"

    def _url(url):
        """Create a regex URL pattern."""
        return re.compile(inventory_app.frontend_url + url)

    # Set timeouts
    page.set_default_timeout(10000)  # 10s for actions
    page.set_default_navigation_timeout(15000)  # 15s for navigation

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

    # Attempt login with invalid credentials
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your password").fill("Wrong@1234")
    login_button = page.get_by_role("button", name="Login", exact=True)
    expect(login_button).to_be_visible(timeout=15000)
    expect(login_button).to_be_enabled(timeout=15000)
    login_button.click(timeout=20000)
    expect(page.get_by_text("Invalid username or password")).to_be_visible(
        timeout=15000
    )

    # Navigate to registration page
    register_link = page.get_by_role("link", name="Register here")
    expect(register_link).to_be_visible(timeout=15000)
    register_link.click(timeout=20000)
    expect(page).to_have_url(_url("/register/"))

    # Attempt registration without confirm password
    page.get_by_placeholder("Enter your ID").fill(TEST_ID)
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your email").fill(TEST_EMAIL)
    page.get_by_placeholder("Enter your password").fill(TEST_PASSWORD)
    signup_button = page.get_by_role("button", name="Sign Up", exact=True)
    expect(signup_button).to_be_visible(timeout=15000)
    expect(signup_button).to_be_enabled(timeout=15000)
    signup_button.click(timeout=20000)
    # Use partial text match to handle potential message variations
    expect(page.get_by_text("Password", exact=True)).to_be_visible(timeout=15000)

    # Complete registration with confirm password
    page.get_by_placeholder("Enter your ID").fill(TEST_ID)
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your email").fill(TEST_EMAIL)
    page.get_by_placeholder("Enter your password").fill(TEST_PASSWORD)
    page.get_by_placeholder("Confirm your password").fill(TEST_PASSWORD)
    expect(signup_button).to_be_visible(timeout=15000)
    signup_button.click(timeout=20000)
    expect(page).to_have_url(_url("/login/"))

    # Login as regular user
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your password").fill(TEST_PASSWORD)
    expect(login_button).to_be_visible(timeout=15000)
    login_button.click(timeout=20000)
    expect(page).to_have_url(_url("/overview/"))  # Employee redirect

    # Verify username in UI
    expect(page.get_by_text(TEST_USERNAME)).to_be_visible(timeout=15000)

    # Logout
    logout_button = page.locator("//*[contains(text(), 'Logout')]")
    expect(logout_button).to_be_visible(timeout=15000)
    logout_button.click(timeout=20000)
    expect(page).to_have_url(_url("/"))

    # Register an admin user
    page.goto(inventory_app.frontend_url + "/register/")
    page.get_by_placeholder("Enter your ID").fill(ADMIN_ID)
    page.get_by_placeholder("Enter your username").fill(ADMIN_USERNAME)
    page.get_by_placeholder("Enter your email").fill(ADMIN_EMAIL)
    page.get_by_placeholder("Enter your password").fill(ADMIN_PASSWORD)
    page.get_by_placeholder("Confirm your password").fill(ADMIN_PASSWORD)
    signup_button = page.get_by_role("button", name="Sign Up", exact=True)
    expect(signup_button).to_be_visible(timeout=15000)
    signup_button.click(timeout=20000)
    expect(page).to_have_url(_url("/login/"))

    # Set admin role manually
    with rx.session() as session:
        admin_user = session.exec(
            LocalUser.select().where(LocalUser.username == ADMIN_USERNAME)
        ).one_or_none()
        assert admin_user, "Admin user not found"
        user_info = session.exec(
            UserInfo.select().where(UserInfo.user_id == admin_user.id)
        ).one_or_none()
        assert user_info, "User info not found"
        user_info.is_admin = True
        user_info.set_role()
        session.add(user_info)
        session.commit()

    # Login as admin
    page.get_by_placeholder("Enter your username").fill(ADMIN_USERNAME)
    page.get_by_placeholder("Enter your password").fill(ADMIN_PASSWORD)
    expect(login_button).to_be_visible(timeout=15000)
    login_button.click(timeout=20000)
    expect(page).to_have_url(_url("/admin/"))  # Admin redirect

    # Verify admin username
    expect(page.get_by_text(ADMIN_USERNAME)).to_be_visible(timeout=15000)

    # Attempt to re-register existing username
    page.goto(inventory_app.frontend_url + "/register/")
    page.get_by_placeholder("Enter your ID").fill(TEST_ID)
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your email").fill(TEST_EMAIL)
    page.get_by_placeholder("Enter your password").fill(TEST_PASSWORD)
    page.get_by_placeholder("Confirm your password").fill(TEST_PASSWORD)
    expect(signup_button).to_be_visible(timeout=15000)
    signup_button.click(timeout=20000)
    expect(
        page.get_by_text(f"Username {TEST_USERNAME} is already registered", exact=False)
    ).to_be_visible(timeout=15000)

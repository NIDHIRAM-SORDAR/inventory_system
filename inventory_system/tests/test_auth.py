from __future__ import annotations

import re
from pathlib import Path

import pytest
import reflex as rx
from playwright.sync_api import Page, expect
from reflex.testing import AppHarness
from reflex_local_auth import LocalUser

from inventory_system.models.user import UserInfo

# Constants for test user
TEST_USERNAME = "test_user"
TEST_PASSWORD = (
    "Test@1234"  # Meets password requirements (8+ chars, upper, lower, number, special)
)
TEST_EMAIL = "test@example.com"
TEST_ID = "12345"
ADMIN_USERNAME = "admin_user"
ADMIN_PASSWORD = "Admin@1234"
ADMIN_EMAIL = "admin@example.com"
ADMIN_ID = "67890"

# XPaths and selectors
LOGIN_BUTTON_XPATH = "//button[contains(text(), 'Login')]"
REGISTER_BUTTON_XPATH = "//button[contains(text(), 'Sign Up')]"
REGISTER_LINK_XPATH = "//a[contains(text(), 'Register here')]"
LOGOUT_XPATH = "//*[contains(text(), 'Logout')]"


@pytest.fixture(scope="session")
def inventory_app():
    """Fixture to start the inventory app using AppHarness."""
    with AppHarness.create(
        root=Path(__file__).parent.parent.parent, app_name="inventory_system"
    ) as harness:
        yield harness


@pytest.fixture(scope="session")
def test_users_cleaned_up():
    """Fixture to clean up test users before tests."""
    with rx.session() as session:
        for username in [TEST_USERNAME, ADMIN_USERNAME]:
            test_user = session.exec(
                LocalUser.select().where(LocalUser.username == username)
            ).one_or_none()
            if test_user is not None:
                session.delete(test_user)
        session.commit()


@pytest.mark.usefixtures("test_users_cleaned_up")
def test_auth_flow(inventory_app: AppHarness, page: Page):
    """Test the authentication flow of the inventory app."""
    assert inventory_app.frontend_url is not None

    def _url(url):
        """Helper to create a regex URL pattern."""
        return re.compile(inventory_app.frontend_url + url)

    # Configure Playwright to use Microsoft Edge
    page.context.browser  # Ensure browser is initialized
    page.set_default_timeout(5000)  # 5-second timeout for actions

    # Navigate to login page
    page.goto(inventory_app.frontend_url + "/login")
    expect(page).to_have_url(_url("/login/"))

    # Attempt login with invalid credentials
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your password").fill("Wrong@1234")
    page.locator(LOGIN_BUTTON_XPATH).click()
    expect(page.get_by_text("Invalid username or password")).to_be_visible()

    # Navigate to registration page
    page.locator(REGISTER_LINK_XPATH).click()
    expect(page).to_have_url(_url("/register/"))

    # Attempt registration without confirming password
    page.get_by_placeholder("Enter your ID").fill(TEST_ID)
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your email").fill(TEST_EMAIL)
    page.get_by_placeholder("Enter your password").fill(TEST_PASSWORD)
    page.locator(REGISTER_BUTTON_XPATH).click()
    expect(page.get_by_text("Passwords do not match")).to_be_visible()

    # Complete registration
    page.get_by_placeholder("Confirm your password").fill(TEST_PASSWORD)
    page.locator(REGISTER_BUTTON_XPATH).click()
    expect(page).to_have_url(_url("/login/"))

    # Login as regular user
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your password").fill(TEST_PASSWORD)
    page.locator(LOGIN_BUTTON_XPATH).click()
    expect(page).to_have_url(_url("/overview/"))  # Employee redirect

    # Verify username in UI (assuming a nav bar or profile section)
    expect(page.get_by_text(TEST_USERNAME)).to_be_visible()

    # Logout
    page.locator(LOGOUT_XPATH).click()
    expect(page).to_have_url(_url("/"))

    # Register an admin user
    page.goto(inventory_app.frontend_url + "/register/")
    page.get_by_placeholder("Enter your ID").fill(ADMIN_ID)
    page.get_by_placeholder("Enter your username").fill(ADMIN_USERNAME)
    page.get_by_placeholder("Enter your email").fill(ADMIN_EMAIL)
    page.get_by_placeholder("Enter your password").fill(ADMIN_PASSWORD)
    page.get_by_placeholder("Confirm your password").fill(ADMIN_PASSWORD)
    page.locator(REGISTER_BUTTON_XPATH).click()
    expect(page).to_have_url(_url("/login/"))

    # Manually set admin role (since app doesn't provide UI for this)
    with rx.session() as session:
        admin_user = session.exec(
            LocalUser.select().where(LocalUser.username == ADMIN_USERNAME)
        ).one_or_none()
        assert admin_user is not None
        user_info = session.exec(
            UserInfo.select().where(UserInfo.user_id == admin_user.id)
        ).one_or_none()
        assert user_info is not None
        user_info.is_admin = True
        user_info.set_role()
        session.add(user_info)
        session.commit()

    # Login as admin
    page.get_by_placeholder("Enter your username").fill(ADMIN_USERNAME)
    page.get_by_placeholder("Enter your password").fill(ADMIN_PASSWORD)
    page.locator(LOGIN_BUTTON_XPATH).click()
    expect(page).to_have_url(_url("/admin/"))  # Admin redirect

    # Verify username
    expect(page.get_by_text(ADMIN_USERNAME)).to_be_visible()

    # Attempt to re-register existing username
    page.goto(inventory_app.frontend_url + "/register/")
    page.get_by_placeholder("Enter your ID").fill(TEST_ID)
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your email").fill(TEST_EMAIL)
    page.get_by_placeholder("Enter your password").fill(TEST_PASSWORD)
    page.get_by_placeholder("Confirm your password").fill(TEST_PASSWORD)
    page.locator(REGISTER_BUTTON_XPATH).click()
    expect(
        page.get_by_text(
            f"Username {TEST_USERNAME} is already registered. Try a different name"
        )
    ).to_be_visible()

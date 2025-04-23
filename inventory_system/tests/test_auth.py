import re
import time

import pytest
import reflex as rx
import reflex_local_auth
from playwright.sync_api import expect
from sqlmodel import select

from inventory_system.models.user import Supplier, UserInfo
from inventory_system.tests.test_utils import edge_page, inventory_app

# Test user constants
TEST_USERNAME = "test_user"
TEST_PASSWORD = "Test@1234"  # Meets password requirements
TEST_EMAIL = "test@example.com"
TEST_ID = "12345"


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


@pytest.mark.usefixtures("test_users_cleaned_up")
def test_logout_flow(inventory_app: inventory_app, edge_page: edge_page):
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
    expect(page).to_have_url(_url("/overview/"), timeout=40000)

    # Verify logged-in state
    expect(page.get_by_role("heading", name=f"Welcome {TEST_USERNAME}")).to_be_visible(
        timeout=25000
    )

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
    )  # .nth(1)(wsl)
    dialog_locator.wait_for(state="visible", timeout=20000)

    expect(dialog_locator).to_contain_text(
        "Are you sure you want to log out?", timeout=15000
    )

    # Click the Confirm button
    confirm_button = dialog_locator.locator('button:has-text("Confirm")')  # .first(wsl)
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

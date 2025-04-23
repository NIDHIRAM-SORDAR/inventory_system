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
TEST_NEW_EMAIL = "newtest@example.com"
TEST_ID = "12345"
INVALID_EMAIL = "invalid_email"
NEW_PASSWORD = "NewPass@5678"  # Meets password requirements
INVALID_PASSWORD = "short"  # Does not meet requirements


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
def test_profile_update_flow(inventory_app: inventory_app, edge_page: edge_page):
    """Test the email and password update flow on the profile page in Microsoft Edge."""
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
    expect(page).to_have_url(_url("/login/"), timeout=25000)

    # Log in as the test user
    page.get_by_placeholder("Enter your username").fill(TEST_USERNAME)
    page.get_by_placeholder("Enter your password").fill(TEST_PASSWORD)
    login_button = page.get_by_role("button", name="Login", exact=True)
    expect(login_button).to_be_enabled(timeout=15000)
    login_button.click()
    expect(page).to_have_url(_url("/overview/"), timeout=40000)

    # Verify logged-in state
    # Verify logged-in state
    expect(page.get_by_role("heading", name=f"Welcome {TEST_USERNAME}")).to_be_visible(
        timeout=35000
    )

    # Navigate to profile page
    navbar = page.get_by_role("navigation")
    dropdown_trigger = navbar.get_by_test_id("user-avatar")
    expect(dropdown_trigger).to_be_visible(timeout=15000)
    dropdown_trigger.click()
    profile_link = page.get_by_role("menuitem").filter(has=page.get_by_text("Profile"))
    expect(profile_link).to_be_visible(timeout=15000)
    profile_link.click(timeout=20000)
    expect(page).to_have_url(_url("/profile/"), timeout=20000)

    # Verify profile page content
    expect(page.get_by_role("heading", name="Personal information")).to_be_visible(
        timeout=20000
    )
    expect(page.get_by_role("heading", name="Change Password")).to_be_visible(
        timeout=20000
    )

    # Test email update with invalid email
    email_input = page.get_by_placeholder("user@reflex.dev")
    email_input.fill(INVALID_EMAIL)
    email_input.blur()  # Trigger on_blur validation
    callout_error = page.locator('div[role="alert"]:has-text("must")')
    # Partial match for email-validator error
    expect(callout_error).to_be_visible(timeout=10000)
    expect(callout_error).to_contain_text("must", timeout=10000)
    # Partial match for "The email address is not valid"

    # Test email update with valid email
    email_input.fill(TEST_NEW_EMAIL)
    email_input.blur()  # Trigger on_blur validation
    update_button = page.get_by_role("button", name="Update").first
    expect(update_button).to_be_enabled(timeout=20000)
    update_button.click()

    # Wait for and verify success toast
    toast_success = page.locator(
        (
            '[data-sonner-toast][data-type="success"]'
            ':has-text("Profile email updated successfully")'
        )
    )
    expect(toast_success).to_be_visible(timeout=15000)
    expect(toast_success).to_contain_text(
        "Profile email updated successfully", timeout=15000
    )

    # Verify email input reflects new email
    expect(email_input).to_have_value(TEST_NEW_EMAIL, timeout=15000)

    # Test password update with invalid password
    current_password_input = page.get_by_placeholder("Enter current password")
    new_password_input = page.get_by_placeholder("Enter new password")
    confirm_password_input = page.get_by_placeholder("Confirm new password")
    password_button = page.get_by_role("button", name="Change Password")

    current_password_input.fill(TEST_PASSWORD)
    new_password_input.fill(INVALID_PASSWORD)
    confirm_password_input.fill(INVALID_PASSWORD)
    expect(password_button).to_be_enabled(timeout=15000)
    password_button.click()

    # Wait for and verify error toast
    toast_error = page.locator(
        (
            '[data-sonner-toast][data-type="error"]'
            ':has-text("Password must be at least 8 characters")'
        )
    )
    expect(toast_error).to_be_visible(timeout=15000)
    expect(toast_error).to_contain_text(
        "Password must be at least 8 characters", timeout=15000
    )

    # Test password update with valid password
    current_password_input.fill(TEST_PASSWORD)
    new_password_input.fill(NEW_PASSWORD)
    confirm_password_input.fill(NEW_PASSWORD)
    password_button.click()

    # Wait for and verify success toast
    toast_success = page.locator(
        (
            '[data-sonner-toast][data-type="success"]'
            ':has-text("Password updated successfully")'
        )
    )
    expect(toast_success).to_be_visible(timeout=10000)
    expect(toast_success).to_contain_text(
        "Password updated successfully", timeout=10000
    )

    # Verify password fields are cleared (due to reset_on_submit=True)
    expect(current_password_input).to_have_value("", timeout=15000)
    expect(new_password_input).to_have_value("", timeout=15000)
    expect(confirm_password_input).to_have_value("", timeout=15000)

    # Log out
    dropdown_trigger.click()
    logout_button = page.get_by_role("menuitem").filter(has=page.get_by_text("Logout"))
    expect(logout_button).to_be_visible(timeout=15000)
    logout_button.click()

    page.pause()

    # Wait for the logout dialog
    dialog_locator = page.locator(
        '[role="alertdialog"][data-state="open"]:has-text("Log Out")'
    )  # nth(1)
    dialog_locator.wait_for(state="visible", timeout=25000)
    expect(dialog_locator).to_contain_text(
        "Are you sure you want to log out?", timeout=15000
    )

    # Click the Confirm button
    confirm_button = dialog_locator.locator(
        'button:has-text("Confirm")'
    )  # .first(for wsl)
    expect(confirm_button).to_be_visible(timeout=3000)
    confirm_button.click(timeout=50000)

    # Verify navigation to homepage
    expect(page).to_have_url(_url("/"), timeout=50000)
    expect(page.get_by_role("button", name="Get Started")).to_be_visible(timeout=30000)

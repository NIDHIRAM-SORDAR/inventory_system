import re
import time
from pathlib import Path

import pytest
import reflex as rx
import requests
from playwright.sync_api import Page, expect, sync_playwright
from reflex.testing import AppHarness
from sqlmodel import select

from inventory_system.models.user import Supplier

# Test supplier constants
TEST_COMPANY_NAME = "TestSupplier123"
TEST_COMPANY_NAME_ALT = "TestSupplier1234"
TEST_DESCRIPTION = "A test supplier for inventory system."
TEST_EMAIL = "testsupplier@gmail.com"
TEST_PHONE = "+8801234567890"


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
                        f"Waiting for frontend... ({time.time() - start_time:.1f}s, error: {e})"
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
def test_suppliers_cleaned_up():
    """Clean up test suppliers before tests."""
    with rx.session() as session:
        test_supplier = session.exec(
            select(Supplier).where(Supplier.contact_email == TEST_EMAIL)
        ).one_or_none()
        if test_supplier:
            session.delete(test_supplier)
        session.commit()


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


@pytest.mark.usefixtures("test_suppliers_cleaned_up")
def test_supplier_registration(inventory_app: AppHarness, edge_page: Page):
    """Test the supplier registration flow in Microsoft Edge."""
    assert inventory_app.frontend_url, "Frontend URL missing"

    def _url(url):
        """Create a regex URL pattern."""
        return re.compile(inventory_app.frontend_url + url)

    page = edge_page
    print("Starting supplier registration test")

    # Navigate to supplier registration page with retry
    for attempt in range(1, 4):
        try:
            print(f"Navigating to supplier registration page (attempt {attempt}/3)")
            page.goto(inventory_app.frontend_url + "/supplier-register")
            page.wait_for_load_state("networkidle")
            expect(page).to_have_url(_url("/supplier-register"))
            expect(page).to_have_title("Supplier Registration", timeout=30000)
            break
        except Exception as e:
            print(f"Navigation failed: {e}")
            if attempt == 3:
                raise
            time.sleep(2)

    # Verify form is present
    print("Verifying form presence")
    form = page.locator('form:has-text("Supplier Registration")')
    expect(form).to_be_visible(timeout=30000)
    expect(page.get_by_text("Supplier Registration")).to_be_visible(timeout=15000)

    # Fill out the form
    print(f"Filling company name: {TEST_COMPANY_NAME}")
    company_input = page.get_by_placeholder("Enter company name")
    company_input.fill(TEST_COMPANY_NAME)
    expect(company_input).to_have_value(TEST_COMPANY_NAME, timeout=10000)

    print(f"Filling description: {TEST_DESCRIPTION}")
    description_input = page.get_by_placeholder("Describe your company")
    description_input.fill(TEST_DESCRIPTION)
    expect(description_input).to_have_value(TEST_DESCRIPTION, timeout=10000)

    print(f"Filling contact email: {TEST_EMAIL}")
    email_input = page.get_by_placeholder("Enter contact email")
    email_input.fill(TEST_EMAIL)
    expect(email_input).to_have_value(TEST_EMAIL, timeout=10000)

    print(f"Filling contact phone: {TEST_PHONE}")
    phone_input = page.get_by_placeholder("Enter contact phone")
    phone_input.fill(TEST_PHONE)
    expect(phone_input).to_have_value(TEST_PHONE, timeout=10000)

    # Submit the form
    print("Submitting registration form")
    submit_button = page.get_by_role("button", name="Register", exact=True)
    expect(submit_button).to_be_enabled(timeout=15000)
    submit_button.click()

    # Verify success message
    print("Verifying success message")
    print(page.get_by_role("alert"))
    success_message = page.get_by_role("alert").filter(
        has_text=re.compile(r"Registration successful")
    )
    expect(success_message).to_be_visible(timeout=30000)

    # Verify supplier in database
    print("Verifying supplier in database")
    with rx.session() as session:
        supplier = session.exec(
            select(Supplier).where(Supplier.contact_email == TEST_EMAIL)
        ).one_or_none()
        assert supplier, "Supplier not found in database"
        print(
            f"Supplier found: company_name={supplier.company_name}, status={supplier.status}"
        )
        assert supplier.company_name == TEST_COMPANY_NAME
        assert supplier.description == TEST_DESCRIPTION
        assert supplier.contact_phone == TEST_PHONE
        assert supplier.status == "pending"

    # Test error case: duplicate email
    print("Testing duplicate email registration")
    company_input.fill(TEST_COMPANY_NAME_ALT)
    description_input.fill(TEST_DESCRIPTION)
    email_input.fill(TEST_EMAIL)  # Re-fill email to trigger duplicate
    phone_input.fill(TEST_PHONE)
    submit_button.click()
    error_message = page.get_by_role("alert").filter(
        has_text=re.compile(r"email\s+is\s+already\s+registered[.!,;:]?", re.IGNORECASE)
    )
    expect(error_message).to_be_visible(timeout=20000)
    print("Verified error message for duplicate email")

    # Test error case: duplicate company_name
    print("Testing duplicate company name registration")
    company_input.fill(TEST_COMPANY_NAME)
    description_input.fill(TEST_DESCRIPTION)
    email_input.fill(TEST_EMAIL)  # Re-fill email to trigger duplicate
    phone_input.fill(TEST_PHONE)
    submit_button.click()
    error_message = page.get_by_role("alert").filter(
        has_text=re.compile(
            r"company name\s+is\s+already\s+registered[.!,;:]?", re.IGNORECASE
        )
    )
    expect(error_message).to_be_visible(timeout=20000)
    print("Verified error message for duplicate company name")

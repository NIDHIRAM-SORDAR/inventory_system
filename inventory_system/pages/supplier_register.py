# inventory_system/pages/supplier_register.py
import reflex as rx
from inventory_system.templates.template import template
from inventory_system.models import Supplier
from sqlmodel import select
import reflex_local_auth
from email_validator import validate_email, EmailNotValidError
from inventory_system import routes


class SupplierRegisterState(rx.State):
    company_name: str = ""
    description: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    success_message: str = ""
    error_message: str = ""

    def set_company_name(self, value: str):
        self.company_name = value.strip()
        self.clear_messages()

    def set_description(self, value: str):
        self.description = value.strip()
        self.clear_messages()

    def set_contact_email(self, value: str):
        self.contact_email = value.strip()
        self.clear_messages()

    def set_contact_phone(self, value: str):
        self.contact_phone = value.strip()
        self.clear_messages()

    def clear_messages(self):
        """Clear success and error messages."""
        self.success_message = ""
        self.error_message = ""

    def validate_form(self) -> bool:
        """Validate the form fields."""
        if not self.company_name:
            self.error_message = "Company name is required."
            return False
        if not self.description:
            self.error_message = "Description is required."
            return False
        if not self.contact_email:
            self.error_message = "Contact email is required."
            return False
        if not self.contact_phone:
            self.error_message = "Contact phone is required."
            return False
        try:
            validate_email(self.contact_email)
        except EmailNotValidError:
            self.error_message = "Please enter a valid email address."
            return False
        return True

    def register_supplier(self):
        """Handle supplier registration."""
        self.clear_messages()

        # Validate form fields
        if not self.validate_form():
            return

        with rx.session() as session:
            # Check if the email is already used
            existing_supplier = session.exec(
                select(Supplier).where(Supplier.contact_email == self.contact_email)
            ).first()
            if existing_supplier:
                self.error_message = "This email is already registered."
                return

            # Create the supplier record
            supplier = Supplier(
                company_name=self.company_name,
                description=self.description,
                contact_email=self.contact_email,
                contact_phone=self.contact_phone,
                status="pending",
            )
            session.add(supplier)
            session.commit()
            session.refresh(supplier)

            # Clear form and show success message
            self.company_name = ""
            self.description = ""
            self.contact_email = ""
            self.contact_phone = ""
            self.success_message = (
                "Registration successful! Please wait for admin approval."
            )


def supplier_registration_form() -> rx.Component:
    return (
        rx.form(
            rx.vstack(
                rx.heading("Supplier Registration", size="7"),
                rx.cond(
                    SupplierRegisterState.success_message != "",
                    rx.callout(
                        SupplierRegisterState.success_message,
                        icon="loader-circle",
                        color_scheme="green",
                        role="alert",
                        width="100%",
                    ),
                ),
                rx.cond(
                    SupplierRegisterState.error_message != "",
                    rx.callout(
                        SupplierRegisterState.error_message,
                        icon="triangle_alert",
                        color_scheme="red",
                        role="alert",
                        width="100%",
                    ),
                ),
                rx.text("Company Name", weight="bold"),
                rx.input(
                    value=SupplierRegisterState.company_name,
                    on_change=SupplierRegisterState.set_company_name,
                    width="100%",
                    required=True,
                ),
                rx.text("Description", weight="bold"),
                rx.input(
                    value=SupplierRegisterState.description,
                    on_change=SupplierRegisterState.set_description,
                    width="100%",
                    required=True,
                ),
                rx.text("Contact Email", weight="bold"),
                rx.input(
                    value=SupplierRegisterState.contact_email,
                    on_change=SupplierRegisterState.set_contact_email,
                    type="email",
                    width="100%",
                    required=True,
                ),
                rx.text("Contact Phone", weight="bold"),
                rx.input(
                    value=SupplierRegisterState.contact_phone,
                    on_change=SupplierRegisterState.set_contact_phone,
                    width="100%",
                    required=True,
                ),
                rx.button(
                    "Register",
                    type="submit",
                    width="100%",
                    size="3",
                ),
                rx.center(
                    rx.link(
                        "Already registered? Log in here.",
                        href=reflex_local_auth.routes.LOGIN_ROUTE,
                        color="gray",
                    ),
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            on_submit=SupplierRegisterState.register_supplier,
        ),
    )


@template(route=routes.SUPPLIER_REGISTER_ROUTE, title="Supplier Registration")
def supplier_register() -> rx.Component:
    """The supplier registration page."""
    return rx.center(
        rx.card(
            supplier_registration_form(),
            width="400px",
        ),
        padding_top="2em",
        width="100%",
        height="100vh",
        align="center",
        justify="center",
    )

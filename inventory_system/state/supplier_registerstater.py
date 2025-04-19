# inventory_system/pages/supplier_register.py
import re

import reflex as rx
from email_validator import EmailNotValidError, validate_email
from sqlmodel import select

from inventory_system.models.user import Supplier

MAX_COMPANY_NAME_LENGTH = 100  # Example limit
MAX_DESCRIPTION_LENGTH = 500  # Example limit


class SupplierRegisterState(rx.State):
    company_name: str = ""
    description: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    success_message: str = ""
    error_message: str = ""
    is_submitting: bool = False  # Added for loading state

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
        self.success_message = ""
        self.error_message = ""

    def validate_form(self) -> bool:
        if not self.company_name:
            self.error_message = "Company name is required."
            return False
        if len(self.company_name) > MAX_COMPANY_NAME_LENGTH:
            self.error_message = (
                f"Company name cannot exceed {MAX_COMPANY_NAME_LENGTH} characters."
            )
            return False
        if not re.match(r"^[a-zA-Z0-9_]+$", self.company_name):
            self.error_message = (
                "Company name can only contain letters, numbers, and underscores (_)"
            )
            return False
        if not self.description:
            self.error_message = "Description is required."
            return False
        if len(self.description) > MAX_DESCRIPTION_LENGTH:
            self.error_message = (
                f"Description cannot exceed {MAX_DESCRIPTION_LENGTH} characters."
            )
            return False
        if not self.contact_email:
            self.error_message = "Contact email is required."
            return False
        if not self.contact_phone:
            self.error_message = "Contact phone is required."
            return False
        phone_regex = r"^(?:\+88)?\d{7,}$"
        if not re.match(phone_regex, self.contact_phone):
            self.error_message = "Please enter a valid phone number format."
            return False
        try:
            validate_email(self.contact_email)
        except EmailNotValidError:
            self.error_message = "Please enter a valid email address."
            return False
        return True

    async def register_supplier(self):
        self.clear_messages()
        self.is_submitting = True  # Show loading state

        if not self.validate_form():
            self.is_submitting = False
            return

        with rx.session() as session:
            existing_supplier = session.exec(
                select(Supplier).where(Supplier.contact_email == self.contact_email)
            ).first()
            if existing_supplier:
                self.error_message = "This email is already registered."
                self.is_submitting = False
                return

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

            self.company_name = ""
            self.description = ""
            self.contact_email = ""
            self.contact_phone = ""
            self.success_message = (
                "Registration successful! Please wait for admin approval."
            )
            self.is_submitting = False

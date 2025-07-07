# inventory_system/pages/supplier_register.py
import re
import uuid

import reflex as rx
from email_validator import EmailNotValidError, validate_email
from sqlmodel import select

from inventory_system.logging.audit_listeners import (
    with_async_audit_context,
)
from inventory_system.logging.logging import audit_logger
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
        self.is_submitting = True
        ip_address = self.router.session.client_ip
        transaction_id = str(uuid.uuid4())
        audit_logger.info(
            "attempt_supplier_registration",
            company_name=self.company_name,
            contact_email=self.contact_email,
            contact_phone=self.contact_phone,
            ip_address=ip_address,
        )

        if not self.validate_form():
            audit_logger.warning(
                "supplier_registration_failed",
                reason="Form validation failed",
                error_message=self.error_message,
                company_name=self.company_name,
                ip_address=ip_address,
            )
            self.is_submitting = False
            return
        async with with_async_audit_context(
            state=self,
            operation_name="supplier_registration",
            transaction_id=transaction_id,
            submitted_company_name=self.company_name,
            submitted_contact_email=self.contact_email,
        ):
            try:
                with rx.session() as session:
                    # Check for existing supplier with the same company_name
                    existing_supplier_by_name = session.exec(
                        select(Supplier).where(
                            Supplier.company_name == self.company_name
                        )
                    ).first()
                    if existing_supplier_by_name:
                        self.error_message = "This company name is already registered."
                        self.is_submitting = False
                        return
                    # Check for existing supplier with the same contact_email
                    existing_supplier = session.exec(
                        select(Supplier).where(
                            Supplier.contact_email == self.contact_email
                        )
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
                    supplier_id = supplier.id

                    audit_logger.info(
                        "supplier_created",
                        company_name=self.company_name,
                        supplier_id=supplier_id,
                        contact_email=self.contact_email,
                        status=supplier.status,
                        ip_address=ip_address,
                    )

                    self.company_name = ""
                    self.description = ""
                    self.contact_email = ""
                    self.contact_phone = ""
                    self.success_message = (
                        "Registration successful! Please wait for admin approval."
                    )
                    audit_logger.info(
                        "success_supplier_registration",
                        company_name=supplier.company_name,
                        supplier_id=supplier_id,
                        contact_email=supplier.contact_email,
                        ip_address=ip_address,
                    )

            except Exception as e:
                self.error_message = "An unexpected error occurred during registration."
                audit_logger.critical(
                    "supplier_registration_failed_unexpected",
                    reason=str(e),
                    company_name=self.company_name,
                    contact_email=self.contact_email,
                    exception_type=type(e).__name__,
                    ip_address=ip_address,
                )
                session.rollback()
            finally:
                self.is_submitting = False

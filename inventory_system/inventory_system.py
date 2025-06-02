"""Welcome to Reflex!."""

# Import all the pages.
import os

import reflex as rx

from inventory_system.logging.logging import setup_loguru

from . import styles
from .logging.audit_middleware import create_audit_logging_transformer
from .pages import *

# Set the environment variable
os.environ["REFLEX_UPLOADED_FILES_DIR"] = "assets/uploads"
setup_loguru()
# Create the app.
audit_transformer = create_audit_logging_transformer()
app = rx.App(
    style=styles.base_style,
    stylesheets=styles.base_stylesheets,
    api_transformer=audit_transformer,
)

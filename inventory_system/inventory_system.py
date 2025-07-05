"""Welcome to Reflex!."""

# Import all the pages.
import os

import reflex as rx

from inventory_system.logging.logging import setup_loguru

from . import styles
from .logging.audit_setup import initialize_audit_system
from .pages import *

# Set the environment variable
os.environ["REFLEX_UPLOADED_FILES_DIR"] = "assets/uploads"
setup_loguru()
initialize_audit_system()
# Create the app.
app = rx.App(
    style=styles.base_style,
    stylesheets=styles.base_stylesheets,
)

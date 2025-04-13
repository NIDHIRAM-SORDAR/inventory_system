"""Welcome to Reflex!."""

# Import all the pages.
import os

import reflex as rx

from . import styles
from .pages import *

# Set the environment variable
os.environ["REFLEX_UPLOADED_FILES_DIR"] = "assets/uploads"

# Create the app.
app = rx.App(
    style=styles.base_style,
    stylesheets=styles.base_stylesheets,
)

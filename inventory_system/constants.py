# inventory_system/constants.py
import os

# Default profile picture path
DEFAULT_PROFILE_PICTURE = "/icons/profile.png"

LOG_DIR = os.path.join(os.getcwd(), "assets", "logs", "audit_{time}.log")
# Supports log rotation with date-only format
available_colors = [
    "tomato",
    "red",
    "ruby",
    "crimson",
    "plum",
    "purple",
    "violet",
    "iris",
    "indigo",
    "blue",
    "teal",
    "jade",
    "green",
    "grass",
    "brown",
    "orange",
    "gold",
    "bronze",
]

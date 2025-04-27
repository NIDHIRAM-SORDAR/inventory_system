# inventory_system/scripts/seed_all.py
import reflex as rx

from inventory_system.scripts.seed_permissions import seed_permissions
from inventory_system.scripts.seed_roles import seed_roles


def seed_all():
    with rx.session() as session:
        seed_permissions(session)
        seed_roles(session)


if __name__ == "__main__":
    seed_all()

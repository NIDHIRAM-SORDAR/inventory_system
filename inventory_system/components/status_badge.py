import reflex as rx


def _badge(status: str):
    badge_mapping = {
        "supplier": ("check", "Approved", "green"),
        "completed": ("check", "Approved", "green"),
        "pending": ("loader", "Pending", "yellow"),
        "canceled": ("ban", "Canceled", "red"),
    }
    icon, text, color_scheme = badge_mapping.get(
        status, ("loader", "Pending", "yellow")
    )
    return rx.badge(
        rx.icon(icon, size=16),
        text,
        color_scheme=color_scheme,
        radius="large",
        variant="surface",
        size="2",
    )


def status_badge(status: rx.Var[str]) -> rx.Component:
    return rx.match(
        status.lower(),
        ("supplier", _badge("supplier")),
        ("completed", _badge("completed")),
        ("pending", _badge("pending")),
        ("canceled", _badge("canceled")),
        _badge("pending"),
    )

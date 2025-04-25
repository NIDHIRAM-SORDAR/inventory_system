import reflex as rx


def _badge(status: str):
    badge_mapping = {
        "approved": ("check", "Approved", "green"),
        "pending": ("loader", "Pending", "yellow"),
        "revoked": ("ban", "Revoked", "red"),
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
        ("approved", _badge("approved")),
        ("pending", _badge("pending")),
        ("revoked", _badge("revoked")),
        _badge("pending"),
    )

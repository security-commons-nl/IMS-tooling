import reflex as rx
from ims.components.layout import layout


def aims_dashboard_page() -> rx.Component:
    """AIMS Dashboard - AI Management System."""
    return layout(
        rx.vstack(
            rx.text(
                "Het AIMS Dashboard is in ontwikkeling. Hier komt het overzicht van de AI management implementatie.",
                color="gray",
                size="2",
            ),
            spacing="4",
            width="100%",
        ),
        title="AIMS Dashboard",
        subtitle="AI Management System",
    )

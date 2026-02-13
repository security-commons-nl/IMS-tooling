import reflex as rx
from ims.components.layout import layout


def bcms_dashboard_page() -> rx.Component:
    """BCMS Dashboard - Business Continuity Management System."""
    return layout(
        rx.vstack(
            rx.text(
                "Het BCMS Dashboard is in ontwikkeling. Hier komt het overzicht van de business continuity implementatie.",
                color="gray",
                size="2",
            ),
            spacing="4",
            width="100%",
        ),
        title="BCMS Dashboard",
        subtitle="Business Continuity Management System",
    )

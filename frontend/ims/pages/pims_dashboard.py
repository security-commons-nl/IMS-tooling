import reflex as rx
from ims.components.layout import layout


def pims_dashboard_page() -> rx.Component:
    """PIMS Dashboard - Privacy Information Management System."""
    return layout(
        rx.vstack(
            rx.text(
                "Het PIMS Dashboard is in ontwikkeling. Hier komt het overzicht van de privacy-implementatie (AVG/GDPR).",
                color="gray",
                size="2",
            ),
            spacing="4",
            width="100%",
        ),
        title="PIMS Dashboard",
        subtitle="Privacy Information Management System",
    )

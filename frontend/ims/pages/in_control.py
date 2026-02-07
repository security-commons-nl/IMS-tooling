"""
In-Control Dashboard Page — Hiaat 5
"""
import reflex as rx
from ims.state.in_control import InControlState
from ims.components.layout import layout


def scope_status_card(item: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(item["scope_name"], weight="bold", size="3"),
                rx.text(item["scope_type"], size="1", color="gray") if item.get("scope_type") else rx.fragment(),
                spacing="0", align_items="start",
            ),
            rx.spacer(),
            rx.match(
                item["level"],
                ("In control", rx.badge(
                    rx.hstack(rx.icon("circle-check", size=12), rx.text("In control"), spacing="1"),
                    color_scheme="green", variant="soft",
                )),
                ("Beperkt in control", rx.badge(
                    rx.hstack(rx.icon("alert-triangle", size=12), rx.text("Beperkt"), spacing="1"),
                    color_scheme="orange", variant="soft",
                )),
                ("Niet in control", rx.badge(
                    rx.hstack(rx.icon("circle-x", size=12), rx.text("Niet in control"), spacing="1"),
                    color_scheme="red", variant="soft",
                )),
                rx.badge("Niet beoordeeld", color_scheme="gray", variant="outline"),
            ),
            width="100%", align="center",
        ),
        width="100%",
    )


def in_control_content() -> rx.Component:
    return rx.vstack(
        rx.cond(
            InControlState.error != "",
            rx.callout(InControlState.error, icon="circle-alert", color="red", margin_bottom="16px"),
        ),

        # Summary cards
        rx.flex(
            rx.card(
                rx.vstack(
                    rx.text("In control", size="1", color="gray"),
                    rx.text(InControlState.in_control_count, size="5", weight="bold", color="green"),
                    spacing="1", align_items="center",
                ),
                flex="1", min_width="120px",
            ),
            rx.card(
                rx.vstack(
                    rx.text("Beperkt", size="1", color="gray"),
                    rx.text(InControlState.limited_count, size="5", weight="bold", color="orange"),
                    spacing="1", align_items="center",
                ),
                flex="1", min_width="120px",
            ),
            rx.card(
                rx.vstack(
                    rx.text("Niet in control", size="1", color="gray"),
                    rx.text(InControlState.not_in_control_count, size="5", weight="bold", color="red"),
                    spacing="1", align_items="center",
                ),
                flex="1", min_width="120px",
            ),
            gap="4", wrap="wrap", width="100%",
        ),

        # Per-scope list
        rx.cond(
            InControlState.is_loading,
            rx.center(rx.spinner(size="2"), padding="40px"),
            rx.cond(
                InControlState.dashboard_items.length() > 0,
                rx.vstack(
                    rx.foreach(InControlState.dashboard_items, scope_status_card),
                    spacing="2", width="100%", margin_top="16px",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("shield-question", size=32, color="gray"),
                        rx.text("Geen scopes gevonden", color="gray"),
                        spacing="2",
                    ),
                    padding="40px",
                ),
            ),
        ),
        width="100%",
        on_mount=InControlState.load_dashboard,
    )


def in_control_page() -> rx.Component:
    return layout(
        in_control_content(),
        title="In-Control Status",
        subtitle="Overzicht van de beheersingsstatus per scope",
    )

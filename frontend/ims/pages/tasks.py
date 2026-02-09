"""
Mijn Taken - Dedicated tasks page
"""
import reflex as rx
from ims.state.dashboard import DashboardState
from ims.components.layout import layout


def _task_row(task: dict) -> rx.Component:
    """Single task row."""
    return rx.table.row(
        rx.table.cell(
            rx.badge(
                task["type"],
                variant="soft",
                color_scheme=rx.cond(
                    task["type"] == "Approval",
                    "purple",
                    rx.cond(
                        task["type"] == "Corrective Action",
                        "red",
                        "blue",
                    ),
                ),
                size="1",
            ),
        ),
        rx.table.cell(rx.text(task["title"], size="2")),
        rx.table.cell(rx.text(task["status"], size="2", color="gray")),
        rx.table.cell(
            rx.badge(
                task["priority"],
                variant="soft",
                color_scheme=rx.cond(
                    task["priority"] == "High",
                    "red",
                    rx.cond(
                        task["priority"] == "Medium",
                        "orange",
                        "gray",
                    ),
                ),
                size="1",
            ),
        ),
    )


def tasks_content() -> rx.Component:
    """Tasks page content."""
    return rx.vstack(
        # Summary badges
        rx.flex(
            rx.cond(
                DashboardState.tasks_overdue > 0,
                rx.badge(
                    rx.fragment(DashboardState.tasks_overdue, " te laat"),
                    color_scheme="red", variant="solid", size="2",
                ),
                rx.fragment(),
            ),
            rx.cond(
                DashboardState.tasks_due_soon > 0,
                rx.badge(
                    rx.fragment(DashboardState.tasks_due_soon, " binnenkort"),
                    color_scheme="orange", variant="soft", size="2",
                ),
                rx.fragment(),
            ),
            rx.badge(
                rx.fragment(DashboardState.tasks_total, " totaal"),
                color_scheme="gray", variant="soft", size="2",
            ),
            gap="3", wrap="wrap",
        ),

        # Quick actions
        rx.flex(
            rx.button(
                rx.icon("plus", size=16),
                "Nieuw Risico",
                variant="soft",
                on_click=rx.redirect("/risks"),
            ),
            rx.button(
                rx.icon("clipboard-check", size=16),
                "Start Assessment",
                variant="soft",
                on_click=rx.redirect("/assessments"),
            ),
            rx.button(
                rx.icon("circle-alert", size=16),
                "Meld Incident",
                variant="soft",
                color_scheme="red",
                on_click=rx.redirect("/incidents"),
            ),
            wrap="wrap",
            gap="2",
        ),

        # Tasks table
        rx.cond(
            DashboardState.tasks_loading,
            rx.center(rx.spinner(size="3"), padding="40px"),
            rx.cond(
                DashboardState.has_tasks,
                rx.card(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Type"),
                                rx.table.column_header_cell("Titel"),
                                rx.table.column_header_cell("Status"),
                                rx.table.column_header_cell("Prioriteit"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(DashboardState.my_tasks, _task_row),
                        ),
                        width="100%",
                    ),
                    padding="16px",
                    width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("circle-check", size=48, color="var(--green-9)"),
                        rx.text("Geen openstaande taken", size="3", color="gray"),
                        align="center", spacing="2",
                    ),
                    padding="60px",
                ),
            ),
        ),

        width="100%",
        spacing="4",
        on_mount=DashboardState.load_dashboard_data,
    )


def tasks_page() -> rx.Component:
    """Tasks page with layout."""
    return layout(
        tasks_content(),
        title="Mijn Taken",
        subtitle="Openstaande taken en acties",
    )

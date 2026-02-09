"""
Corrective Actions Page - Verbeteracties (PDCA Act)
"""
import reflex as rx
from ims.state.corrective_action import CorrectiveActionState
from ims.state.auth import AuthState
from ims.components.layout import layout


def priority_badge(priority: str) -> rx.Component:
    """Badge for action priority."""
    return rx.match(
        priority,
        ("Low", rx.badge("Laag", color_scheme="green", variant="soft")),
        ("Medium", rx.badge("Gemiddeld", color_scheme="yellow", variant="soft")),
        ("High", rx.badge("Hoog", color_scheme="orange", variant="soft")),
        ("Critical", rx.badge("Kritiek", color_scheme="red", variant="soft")),
        rx.badge(priority, color_scheme="gray", variant="outline"),
    )


def source_badge(item: dict) -> rx.Component:
    """Badge showing the source type of the corrective action."""
    return rx.cond(
        item["risk_id"],
        rx.badge("Risico", color_scheme="orange", variant="surface", size="1"),
        rx.cond(
            item["control_id"],
            rx.badge("Control", color_scheme="blue", variant="surface", size="1"),
            rx.cond(
                item["finding_id"],
                rx.badge("Finding", color_scheme="purple", variant="surface", size="1"),
                rx.cond(
                    item["incident_id"],
                    rx.badge("Incident", color_scheme="red", variant="surface", size="1"),
                    rx.cond(
                        item["issue_id"],
                        rx.badge("Issue", color_scheme="yellow", variant="surface", size="1"),
                        rx.cond(
                            item["initiative_id"],
                            rx.badge("Initiatief", color_scheme="green", variant="surface", size="1"),
                            rx.badge("Los", color_scheme="gray", variant="surface", size="1"),
                        ),
                    ),
                ),
            ),
        ),
    )


def status_indicator(item: dict) -> rx.Component:
    """Status indicator for the corrective action."""
    return rx.cond(
        item["verified"],
        rx.badge(
            rx.hstack(rx.icon("shield-check", size=10), rx.text("Geverifieerd"), spacing="1"),
            color_scheme="green", variant="soft", size="1",
        ),
        rx.cond(
            item["completed"],
            rx.badge(
                rx.hstack(rx.icon("check", size=10), rx.text("Afgerond"), spacing="1"),
                color_scheme="blue", variant="soft", size="1",
            ),
            rx.badge("Open", color_scheme="gray", variant="soft", size="1"),
        ),
    )


def due_date_cell(item: dict) -> rx.Component:
    """Due date with overdue warning."""
    return rx.cond(
        item["due_date"],
        rx.text(
            item["due_date"].to(str)[:10],
            size="2",
            color=rx.cond(
                item["completed"],
                "gray",
                "inherit",
            ),
        ),
        rx.text("-", size="2", color="gray"),
    )


def action_buttons(item: dict) -> rx.Component:
    """Action buttons for a corrective action row."""
    return rx.hstack(
        # Complete button (only if not completed)
        rx.cond(
            ~item["completed"],
            rx.tooltip(
                rx.icon_button(
                    rx.icon("check", size=14),
                    variant="ghost",
                    size="1",
                    color_scheme="green",
                    on_click=lambda: CorrectiveActionState.complete_action(item["id"]),
                ),
                content="Afronden",
            ),
        ),
        # Verify button (only if completed but not verified)
        rx.cond(
            item["completed"] & ~item["verified"],
            rx.tooltip(
                rx.icon_button(
                    rx.icon("shield-check", size=14),
                    variant="ghost",
                    size="1",
                    color_scheme="blue",
                    on_click=lambda: CorrectiveActionState.verify_action(item["id"]),
                ),
                content="Verifieer",
            ),
        ),
        # Edit button
        rx.cond(
            AuthState.can_edit,
            rx.icon_button(
                rx.icon("pencil", size=14),
                variant="ghost",
                size="1",
                on_click=lambda: CorrectiveActionState.open_edit_dialog(item["id"]),
            ),
        ),
        # Delete button
        rx.cond(
            AuthState.can_edit,
            rx.icon_button(
                rx.icon("trash-2", size=14),
                variant="ghost",
                size="1",
                color_scheme="red",
                on_click=lambda: CorrectiveActionState.open_delete_dialog(item["id"]),
            ),
        ),
        spacing="1",
    )


def action_row(item: dict) -> rx.Component:
    """Single row in the corrective actions table."""
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(item["title"], weight="medium", size="2"),
                rx.cond(
                    item["description"],
                    rx.text(item["description"], size="1", color="gray", no_of_lines=1),
                ),
                align_items="start",
                spacing="0",
            ),
        ),
        rx.table.cell(source_badge(item)),
        rx.table.cell(priority_badge(item["priority"])),
        rx.table.cell(status_indicator(item)),
        rx.table.cell(due_date_cell(item)),
        rx.table.cell(action_buttons(item)),
        _hover={"background": "var(--gray-a3)"},
    )


def action_mobile_card(item: dict) -> rx.Component:
    """Mobile card view for a single corrective action."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(item["title"], weight="medium", size="2", flex="1"),
                action_buttons(item),
                width="100%",
                align="center",
            ),
            rx.cond(
                item["description"],
                rx.text(item["description"], size="1", color="gray", no_of_lines=2),
            ),
            rx.hstack(
                source_badge(item),
                priority_badge(item["priority"]),
                status_indicator(item),
                rx.cond(
                    item["due_date"],
                    rx.text(item["due_date"].to(str)[:10], size="1", color="gray"),
                ),
                spacing="2",
                wrap="wrap",
            ),
            spacing="2",
            width="100%",
        ),
        width="100%",
    )


def actions_table() -> rx.Component:
    """Corrective actions data table."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Titel"),
                rx.table.column_header_cell("Bron", width="90px"),
                rx.table.column_header_cell("Prioriteit", width="100px"),
                rx.table.column_header_cell("Status", width="120px"),
                rx.table.column_header_cell("Deadline", width="100px"),
                rx.table.column_header_cell("Acties", width="140px"),
            ),
        ),
        rx.table.body(
            rx.cond(
                CorrectiveActionState.is_loading,
                rx.table.row(
                    rx.table.cell(
                        rx.center(rx.spinner(size="2"), width="100%", padding="40px"),
                        col_span=6,
                    ),
                ),
                rx.cond(
                    CorrectiveActionState.items.length() > 0,
                    rx.foreach(CorrectiveActionState.items, action_row),
                    rx.table.row(
                        rx.table.cell(
                            rx.center(
                                rx.vstack(
                                    rx.icon("list-checks", size=32, color="gray"),
                                    rx.text("Geen verbeteracties gevonden", color="gray"),
                                    spacing="2",
                                ),
                                width="100%",
                                padding="40px",
                            ),
                            col_span=6,
                        ),
                    ),
                ),
            ),
        ),
        width="100%",
    )


def filter_bar() -> rx.Component:
    """Filter bar for corrective actions."""
    return rx.flex(
        rx.select.root(
            rx.select.trigger(placeholder="Status"),
            rx.select.content(
                rx.select.item("Alle statussen", value="ALLE"),
                rx.select.item("Open", value="OPEN"),
                rx.select.item("Achterstallig", value="ACHTERSTALLIG"),
                rx.select.item("Afgerond", value="AFGEROND"),
                rx.select.item("Geverifieerd", value="GEVERIFIEERD"),
            ),
            value=CorrectiveActionState.filter_status,
            on_change=CorrectiveActionState.set_filter_status,
            size="2",
            default_value="ALLE",
            width=rx.breakpoints(initial="100%", md="auto"),
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Prioriteit"),
            rx.select.content(
                rx.select.item("Alle prioriteiten", value="ALLE"),
                rx.select.item("Laag", value="LOW"),
                rx.select.item("Gemiddeld", value="MEDIUM"),
                rx.select.item("Hoog", value="HIGH"),
                rx.select.item("Kritiek", value="CRITICAL"),
            ),
            value=CorrectiveActionState.filter_priority,
            on_change=CorrectiveActionState.set_filter_priority,
            size="2",
            default_value="ALLE",
            width=rx.breakpoints(initial="100%", md="auto"),
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Bron"),
            rx.select.content(
                rx.select.item("Alle bronnen", value="ALLE"),
                rx.select.item("Finding", value="FINDING"),
                rx.select.item("Incident", value="INCIDENT"),
                rx.select.item("Issue", value="ISSUE"),
                rx.select.item("Initiatief", value="INITIATIVE"),
                rx.select.item("Risico", value="RISK"),
                rx.select.item("Control", value="CONTROL"),
            ),
            value=CorrectiveActionState.filter_source,
            on_change=CorrectiveActionState.set_filter_source,
            size="2",
            default_value="ALLE",
            width=rx.breakpoints(initial="100%", md="auto"),
        ),
        rx.button(
            rx.icon("x", size=14),
            "Reset",
            variant="ghost",
            size="2",
            on_click=CorrectiveActionState.clear_filters,
            width=rx.breakpoints(initial="100%", md="auto"),
        ),
        rx.spacer(display=rx.breakpoints(initial="none", md="block")),
        rx.cond(
            AuthState.can_edit,
            rx.button(
                rx.icon("plus", size=14),
                "Nieuwe actie",
                size="2",
                on_click=CorrectiveActionState.open_create_dialog,
                width=rx.breakpoints(initial="100%", md="auto"),
            ),
        ),
        wrap="wrap",
        gap="2",
        width="100%",
    )


def stat_cards() -> rx.Component:
    """KPI statistics cards."""
    return rx.grid(
        rx.card(
            rx.hstack(
                rx.icon("list-checks", size=20, color="var(--accent-9)"),
                rx.vstack(
                    rx.text("Totaal", size="1", color="gray"),
                    rx.text(CorrectiveActionState.total_count, size="4", weight="bold"),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
            ),
            padding="12px",
        ),
        rx.card(
            rx.hstack(
                rx.icon("circle-dot", size=20, color="var(--orange-9)"),
                rx.vstack(
                    rx.text("Open", size="1", color="gray"),
                    rx.text(CorrectiveActionState.open_count, size="4", weight="bold"),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
            ),
            padding="12px",
        ),
        rx.card(
            rx.hstack(
                rx.icon("clock", size=20, color="var(--red-9)"),
                rx.vstack(
                    rx.text("Achterstallig", size="1", color="gray"),
                    rx.text(
                        CorrectiveActionState.overdue_count,
                        size="4",
                        weight="bold",
                        color=rx.cond(
                            CorrectiveActionState.overdue_count > 0,
                            "var(--red-9)",
                            "inherit",
                        ),
                    ),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
            ),
            padding="12px",
        ),
        rx.card(
            rx.hstack(
                rx.icon("check-circle", size=20, color="var(--green-9)"),
                rx.vstack(
                    rx.text("Afgerond", size="1", color="gray"),
                    rx.text(CorrectiveActionState.completed_count, size="4", weight="bold"),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
            ),
            padding="12px",
        ),
        columns=rx.breakpoints(initial="2", md="4"),
        spacing="3",
        width="100%",
    )


def action_form_dialog() -> rx.Component:
    """Dialog for creating/editing a corrective action."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    CorrectiveActionState.is_editing,
                    "Verbeteractie Bewerken",
                    "Nieuwe Verbeteractie",
                ),
            ),
            rx.dialog.description(
                "Maak een verbeteractie aan of koppel deze aan een risico, control, finding of incident.",
                size="2",
                margin_bottom="16px",
            ),

            rx.cond(
                CorrectiveActionState.error != "",
                rx.callout(
                    CorrectiveActionState.error,
                    icon="circle-alert",
                    color="red",
                    margin_bottom="16px",
                ),
            ),

            rx.vstack(
                # Title
                rx.vstack(
                    rx.text("Titel *", size="2", weight="medium"),
                    rx.input(
                        placeholder="Korte omschrijving van de actie",
                        value=CorrectiveActionState.form_title,
                        on_change=CorrectiveActionState.set_form_title,
                        width="100%",
                    ),
                    align_items="start",
                    width="100%",
                ),

                # Description
                rx.vstack(
                    rx.text("Beschrijving", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Wat moet er gedaan worden?",
                        value=CorrectiveActionState.form_description,
                        on_change=CorrectiveActionState.set_form_description,
                        width="100%",
                        rows="3",
                    ),
                    align_items="start",
                    width="100%",
                ),

                # Type + Priority + Due date
                rx.flex(
                    rx.vstack(
                        rx.text("Type", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(placeholder="Type"),
                            rx.select.content(
                                rx.select.item("Correctief", value="Corrective"),
                                rx.select.item("Preventief", value="Preventive"),
                                rx.select.item("Detectief", value="Detective"),
                            ),
                            value=CorrectiveActionState.form_action_type,
                            on_change=CorrectiveActionState.set_form_action_type,
                        ),
                        align_items="start",
                        flex="1",
                        min_width="140px",
                    ),
                    rx.vstack(
                        rx.text("Prioriteit", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(placeholder="Prioriteit"),
                            rx.select.content(
                                rx.select.item("Laag", value="LOW"),
                                rx.select.item("Gemiddeld", value="MEDIUM"),
                                rx.select.item("Hoog", value="HIGH"),
                                rx.select.item("Kritiek", value="CRITICAL"),
                            ),
                            value=CorrectiveActionState.form_priority,
                            on_change=CorrectiveActionState.set_form_priority,
                        ),
                        align_items="start",
                        flex="1",
                        min_width="140px",
                    ),
                    rx.vstack(
                        rx.text("Deadline", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=CorrectiveActionState.form_due_date,
                            on_change=CorrectiveActionState.set_form_due_date,
                            width="100%",
                        ),
                        align_items="start",
                        flex="1",
                        min_width="140px",
                    ),
                    wrap="wrap",
                    gap="3",
                    width="100%",
                ),

                # Assignee
                rx.vstack(
                    rx.text("Verantwoordelijke", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Kies een gebruiker"),
                        rx.select.content(
                            rx.select.item("Geen", value=""),
                            rx.foreach(
                                CorrectiveActionState.users,
                                lambda u: rx.select.item(
                                    u["display_name"],
                                    value=u["id"].to(str),
                                ),
                            ),
                        ),
                        value=CorrectiveActionState.form_assigned_to_id,
                        on_change=CorrectiveActionState.set_form_assigned_to_id,
                    ),
                    align_items="start",
                    width="100%",
                ),

                rx.divider(),
                rx.text("Koppelingen", weight="bold", size="3"),

                # Risk + Control linking
                rx.flex(
                    rx.vstack(
                        rx.text("Risico", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(placeholder="Koppel aan risico"),
                            rx.select.content(
                                rx.select.item("Geen", value=""),
                                rx.foreach(
                                    CorrectiveActionState.risks,
                                    lambda r: rx.select.item(
                                        r["title"],
                                        value=r["id"].to(str),
                                    ),
                                ),
                            ),
                            value=CorrectiveActionState.form_risk_id,
                            on_change=CorrectiveActionState.set_form_risk_id,
                        ),
                        align_items="start",
                        flex="1",
                        min_width="200px",
                    ),
                    rx.vstack(
                        rx.text("Control", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(placeholder="Koppel aan control"),
                            rx.select.content(
                                rx.select.item("Geen", value=""),
                                rx.foreach(
                                    CorrectiveActionState.controls,
                                    lambda c: rx.select.item(
                                        c["title"],
                                        value=c["id"].to(str),
                                    ),
                                ),
                            ),
                            value=CorrectiveActionState.form_control_id,
                            on_change=CorrectiveActionState.set_form_control_id,
                        ),
                        align_items="start",
                        flex="1",
                        min_width="200px",
                    ),
                    wrap="wrap",
                    gap="3",
                    width="100%",
                ),

                spacing="3",
                width="100%",
            ),

            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Annuleren",
                        variant="soft",
                        color_scheme="gray",
                        on_click=CorrectiveActionState.close_form_dialog,
                    ),
                ),
                rx.button(
                    rx.cond(CorrectiveActionState.is_editing, "Opslaan", "Aanmaken"),
                    on_click=CorrectiveActionState.save_item,
                ),
                spacing="3",
                justify="end",
                margin_top="16px",
            ),

            max_width=rx.breakpoints(initial="95vw", md="650px"),
        ),
        open=CorrectiveActionState.show_form_dialog,
    )


def delete_confirm_dialog() -> rx.Component:
    """Dialog for confirming deletion."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Verbeteractie Verwijderen"),
            rx.alert_dialog.description(
                rx.vstack(
                    rx.text("Weet u zeker dat u deze verbeteractie wilt verwijderen?"),
                    rx.text(CorrectiveActionState.deleting_action_title, weight="bold", color="red"),
                    rx.text("Deze actie kan niet ongedaan worden gemaakt.", size="2", color="gray"),
                    spacing="2",
                    align_items="start",
                ),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Annuleren",
                        variant="soft",
                        color_scheme="gray",
                        on_click=CorrectiveActionState.close_delete_dialog,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Verwijderen",
                        color_scheme="red",
                        on_click=CorrectiveActionState.confirm_delete,
                    ),
                ),
                spacing="3",
                justify="end",
                margin_top="16px",
            ),
        ),
        open=CorrectiveActionState.show_delete_dialog,
    )


def corrective_actions_content() -> rx.Component:
    """Corrective actions page content."""
    return rx.vstack(
        rx.cond(
            CorrectiveActionState.success_message != "",
            rx.callout(
                CorrectiveActionState.success_message,
                icon="circle-check",
                color="green",
                margin_bottom="16px",
            ),
        ),
        rx.cond(
            CorrectiveActionState.error != "",
            rx.callout(
                CorrectiveActionState.error,
                icon="circle-alert",
                color="red",
                margin_bottom="16px",
            ),
        ),

        # Overdue warning
        rx.cond(
            CorrectiveActionState.overdue_count > 0,
            rx.callout(
                rx.vstack(
                    rx.text("Achterstallige acties!", weight="bold"),
                    rx.text(
                        rx.fragment(
                            "Er zijn ",
                            CorrectiveActionState.overdue_count,
                            " verbeteracties waarvan de deadline verstreken is.",
                        ),
                        size="2",
                    ),
                    align_items="start",
                    spacing="1",
                ),
                icon="clock",
                color="red",
                margin_bottom="16px",
            ),
        ),

        stat_cards(),
        filter_bar(),

        # Table (desktop)
        rx.box(
            rx.card(
                actions_table(),
                padding="0",
            ),
            width="100%",
            margin_top="16px",
            display=rx.breakpoints(initial="none", md="block"),
        ),
        # Mobile cards
        rx.box(
            rx.vstack(
                rx.cond(
                    CorrectiveActionState.is_loading,
                    rx.center(rx.spinner(size="2"), padding="40px"),
                    rx.cond(
                        CorrectiveActionState.items.length() > 0,
                        rx.foreach(CorrectiveActionState.items, action_mobile_card),
                        rx.center(
                            rx.text("Geen verbeteracties gevonden", color="gray"),
                            padding="40px",
                        ),
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            width="100%",
            margin_top="16px",
            display=rx.breakpoints(initial="block", md="none"),
        ),

        # Dialogs
        action_form_dialog(),
        delete_confirm_dialog(),

        width="100%",
        spacing="4",
        on_mount=CorrectiveActionState.load_all,
    )


def corrective_actions_page() -> rx.Component:
    """Corrective actions page with layout."""
    return layout(
        corrective_actions_content(),
        title="Verbeteracties",
        subtitle="Verbeteracties en opvolging (PDCA Act)",
    )

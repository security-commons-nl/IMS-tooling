"""
Layout Components - Hamburger navigation with push sidebar
Single sidebar: temporarily open (hamburger) or pinned (user toggle).
Content pushes right when sidebar is visible — no overlay/drawer.
"""
import reflex as rx
from ims.state.auth import AuthState
from ims.state.base import BaseState
from ims.state.chat import ChatState
from ims.components.chat_island import chat_island


# ---------------------------------------------------------------------------
# Navigation link helper
# ---------------------------------------------------------------------------

def sidebar_nav_link(label: str, href: str, icon: str) -> rx.Component:
    """Navigation link — closes sidebar on click when not pinned."""
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=20),
            rx.text(label, size="2"),
            width="100%",
            padding="8px 12px",
            border_radius="md",
            _hover={"background": "var(--gray-a3)"},
        ),
        href=href,
        width="100%",
        text_decoration="none",
        color="inherit",
        on_click=BaseState.nav_link_close,
    )


def _section_header(label: str, is_open_var, toggle_handler):
    """Clickable section header with chevron."""
    return rx.hstack(
        rx.text(label, size="1", weight="bold", color="gray"),
        rx.spacer(),
        rx.cond(
            is_open_var,
            rx.icon("chevron-down", size=14, color="gray"),
            rx.icon("chevron-right", size=14, color="gray"),
        ),
        on_click=toggle_handler,
        cursor="pointer",
        padding="8px 12px 4px",
        width="100%",
        align="center",
        _hover={"background": "var(--gray-a2)"},
        border_radius="md",
    )


def _build_nav_links(link_fn):
    """Build the full list of navigation items for a given link function.

    Sections are collapsible. MS Hub is always visible at the top.
    - DOEN: default open
    - ONTDEKKEN: default closed
    - INRICHTEN: default closed, only for configurers
    - BEHEER: default closed, only for user managers
    """
    return [
        # MS Hub — always visible at top
        link_fn("MS Hub", "/ms-hub", "layout-grid"),
        link_fn("Dashboard", "/", "layout-dashboard"),
        rx.divider(margin_y="4px"),
        # DOEN — collapsible, default open
        _section_header("DOEN", BaseState.menu_doen_open, BaseState.toggle_menu_doen),
        rx.cond(
            BaseState.menu_doen_open,
            rx.fragment(
                link_fn("Risico's", "/risks", "triangle-alert"),
                link_fn("Controls", "/controls", "shield-check"),
                link_fn("Compliance", "/compliance", "clipboard-list"),
                link_fn("Assessments", "/assessments", "clipboard-check"),
                link_fn("Incidenten", "/incidents", "circle-alert"),
                link_fn("Besluiten", "/decisions", "stamp"),
                link_fn("In-Control", "/in-control", "gauge"),
            ),
        ),
        rx.divider(margin_y="4px"),
        # ONTDEKKEN — collapsible, default closed
        _section_header("ONTDEKKEN", BaseState.menu_ontdekken_open, BaseState.toggle_menu_ontdekken),
        rx.cond(
            BaseState.menu_ontdekken_open,
            rx.fragment(
                link_fn("Frameworks", "/frameworks", "library"),
                link_fn("Maatregelen", "/measures", "book-open"),
                link_fn("Uitgangspunten", "/policy-principles", "link-2"),
                link_fn("Risicokader", "/risk-framework", "ruler"),
                link_fn("Analyses", "/simulation", "chart-bar"),
                link_fn("Rapportage", "/reports", "file-chart-column"),
                link_fn("Backlog", "/backlog", "list-todo"),
            ),
        ),
        # INRICHTEN — only for configurers (Beheerder, Coordinator, Eigenaar)
        rx.cond(
            AuthState.can_configure,
            rx.fragment(
                rx.divider(margin_y="4px"),
                _section_header("INRICHTEN", BaseState.menu_inrichten_open, BaseState.toggle_menu_inrichten),
                rx.cond(
                    BaseState.menu_inrichten_open,
                    rx.fragment(
                        link_fn("Beleid", "/policies", "file-text"),
                        link_fn("Scopes", "/scopes", "git-branch"),
                        link_fn("Assets", "/assets", "server"),
                        link_fn("Leveranciers", "/suppliers", "building-2"),
                    ),
                ),
            ),
        ),
        # BEHEER — only for user managers (Beheerder, Coordinator)
        rx.cond(
            AuthState.can_manage_users,
            rx.fragment(
                rx.divider(margin_y="4px"),
                _section_header("BEHEER", BaseState.menu_beheer_open, BaseState.toggle_menu_beheer),
                rx.cond(
                    BaseState.menu_beheer_open,
                    rx.fragment(
                        link_fn("Gebruikers", "/users", "users"),
                        rx.cond(
                            AuthState.is_admin,
                            link_fn("Beheer", "/admin", "settings"),
                        ),
                    ),
                ),
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Top bar (hamburger) — shown when sidebar is hidden
# ---------------------------------------------------------------------------

def top_bar() -> rx.Component:
    """Sticky top bar with hamburger menu."""
    return rx.box(
        rx.hstack(
            rx.icon_button(
                rx.icon("menu", size=22),
                variant="ghost",
                size="3",
                on_click=BaseState.toggle_sidebar,
            ),
            rx.hstack(
                rx.icon("shield-check", size=22, color="var(--accent-9)"),
                rx.text("IMS", size="4", weight="bold"),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.icon_button(
                rx.color_mode_cond(
                    light=rx.icon("moon", size=16),
                    dark=rx.icon("sun", size=16),
                ),
                variant="ghost",
                size="2",
                on_click=rx.toggle_color_mode,
            ),
            width="100%",
            padding="8px 12px",
            align="center",
        ),
        border_bottom="1px solid var(--gray-a5)",
        background="var(--color-background)",
        position="sticky",
        top="0",
        z_index="10",
    )


# ---------------------------------------------------------------------------
# Push sidebar — replaces both drawer and pinned sidebar
# ---------------------------------------------------------------------------

def sidebar() -> rx.Component:
    """Push sidebar — visible when open or pinned, pushes content right."""
    return rx.box(
        rx.vstack(
            # Header with pin toggle and close button
            rx.hstack(
                rx.icon("shield-check", size=28, color="var(--accent-9)"),
                rx.text("IMS", size="5", weight="bold"),
                rx.spacer(),
                # Pin toggle
                rx.icon_button(
                    rx.cond(
                        BaseState.sidebar_pinned,
                        rx.icon("pin-off", size=18),
                        rx.icon("pin", size=18),
                    ),
                    variant=rx.cond(
                        BaseState.sidebar_pinned,
                        "solid",
                        "outline",
                    ),
                    color_scheme="indigo",
                    size="2",
                    on_click=BaseState.toggle_pin,
                ),
                # Close (X)
                rx.icon_button(
                    rx.icon("x", size=20),
                    variant="ghost",
                    size="2",
                    on_click=BaseState.close_sidebar,
                ),
                width="100%",
                padding="16px",
                align="center",
            ),
            rx.divider(),

            # Navigation
            rx.vstack(
                *_build_nav_links(sidebar_nav_link),
                spacing="1",
                width="100%",
                padding="8px",
                overflow_y="auto",
                flex="1",
            ),

            rx.divider(),

            # User section
            rx.hstack(
                rx.avatar(
                    fallback=AuthState.user_display_name[0],
                    size="2",
                ),
                rx.vstack(
                    rx.text(AuthState.user_display_name, size="2", weight="medium"),
                    rx.text(AuthState.user_email, size="1", color="gray"),
                    spacing="0",
                    align_items="start",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.color_mode_cond(
                        light=rx.icon("moon", size=16),
                        dark=rx.icon("sun", size=16),
                    ),
                    variant="ghost",
                    size="1",
                    on_click=rx.toggle_color_mode,
                ),
                rx.icon_button(
                    rx.icon("log-out", size=16),
                    variant="ghost",
                    size="1",
                    on_click=AuthState.logout,
                ),
                width="100%",
                padding="12px",
            ),

            height="100vh",
            width="100%",
            align_items="stretch",
        ),
        width="260px",
        min_width="260px",
        background="var(--gray-a2)",
        border_right="1px solid var(--gray-a5)",
    )


# ---------------------------------------------------------------------------
# Page header + main layout
# ---------------------------------------------------------------------------

def page_header(title: str, subtitle: str = "") -> rx.Component:
    """Page header with title — responsive padding and font size."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.heading(title, size=rx.breakpoints(initial="5", md="6")),
                rx.cond(
                    subtitle != "",
                    rx.text(subtitle, size="2", color="gray"),
                ),
                align_items="start",
                spacing="1",
            ),
            rx.spacer(),
            width="100%",
        ),
        padding=rx.breakpoints(initial="12px 16px", md="24px"),
        border_bottom="1px solid var(--gray-a5)",
    )


def layout(content: rx.Component, title: str = "", subtitle: str = "") -> rx.Component:
    """Main layout wrapper with push sidebar and optional pin.

    The sidebar pushes content right when visible — no overlay/drawer.
    """
    return rx.cond(
        AuthState.is_authenticated,
        rx.fragment(
            rx.hstack(
                # Sidebar: visible when open or pinned, pushes content
                rx.cond(
                    BaseState.sidebar_visible,
                    sidebar(),
                    rx.fragment(),
                ),
                # Main content area
                rx.box(
                    # Top bar: only when sidebar is hidden
                    rx.cond(
                        BaseState.sidebar_visible,
                        rx.fragment(),
                        top_bar(),
                    ),
                    rx.cond(
                        title != "",
                        page_header(title, subtitle),
                        rx.fragment(),
                    ),
                    rx.box(
                        content,
                        padding=rx.breakpoints(initial="12px", md="24px"),
                        overflow_y="auto",
                        flex="1",
                    ),
                    flex="1",
                    height="100vh",
                    overflow="hidden",
                    display="flex",
                    flex_direction="column",
                    on_mount=ChatState.sync_page_context,
                ),
                width="100%",
                spacing="0",
            ),
            chat_island(),
        ),
        # Not (yet) authenticated — client-side localStorage check avoids
        # server-side hydration race: the browser knows immediately whether
        # the user is logged in, no WebSocket round-trip needed.
        rx.fragment(
            rx.center(
                rx.spinner(size="3"),
                height="100vh",
            ),
            rx.script(
                "if(!localStorage.getItem('ims_user'))window.location.href='/login';"
            ),
        ),
    )

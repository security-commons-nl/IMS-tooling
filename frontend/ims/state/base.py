"""
Base State - shared state across the application
"""
import reflex as rx
from typing import Optional


class BaseState(rx.State):
    """Base state with common functionality."""

    # Current tenant context
    current_tenant_id: int = 1

    # Loading states
    is_loading: bool = False
    error_message: str = ""

    # Toast notifications
    toast_message: str = ""
    toast_type: str = "info"  # info, success, error, warning

    # Sidebar (push sidebar + optional pin)
    sidebar_open: bool = False
    sidebar_pinned: bool = False

    # Journey stepper (collapsible on MS Hub)
    journey_expanded: bool = True

    # Collapsible menu sections
    menu_doen_open: bool = True
    menu_ontdekken_open: bool = False
    menu_inrichten_open: bool = False
    menu_beheer_open: bool = False

    @rx.var
    def sidebar_visible(self) -> bool:
        """Sidebar is visible when temporarily open OR pinned."""
        return self.sidebar_open or self.sidebar_pinned

    def toggle_sidebar(self):
        """Toggle sidebar — opens if hidden, closes completely if visible."""
        if self.sidebar_open or self.sidebar_pinned:
            self.sidebar_open = False
            self.sidebar_pinned = False
        else:
            self.sidebar_open = True

    def close_sidebar(self):
        """Close sidebar completely (X button)."""
        self.sidebar_open = False
        self.sidebar_pinned = False

    def toggle_pin(self):
        """Toggle pin. Unpinning also closes the sidebar."""
        if self.sidebar_pinned:
            self.sidebar_pinned = False
            self.sidebar_open = False
        else:
            self.sidebar_pinned = True

    def nav_link_close(self):
        """Close sidebar after nav-link click — only when not pinned."""
        if not self.sidebar_pinned:
            self.sidebar_open = False

    def toggle_journey_expanded(self):
        """Toggle journey stepper visibility."""
        self.journey_expanded = not self.journey_expanded

    def toggle_menu_doen(self):
        self.menu_doen_open = not self.menu_doen_open

    def toggle_menu_ontdekken(self):
        self.menu_ontdekken_open = not self.menu_ontdekken_open

    def toggle_menu_inrichten(self):
        self.menu_inrichten_open = not self.menu_inrichten_open

    def toggle_menu_beheer(self):
        self.menu_beheer_open = not self.menu_beheer_open

    def set_loading(self, loading: bool):
        """Set loading state."""
        self.is_loading = loading

    def set_error(self, message: str):
        """Set error message."""
        self.error_message = message
        self.toast_message = message
        self.toast_type = "error"

    def clear_error(self):
        """Clear error message."""
        self.error_message = ""

    def show_toast(self, message: str, toast_type: str = "info"):
        """Show toast notification."""
        self.toast_message = message
        self.toast_type = toast_type

    def clear_toast(self):
        """Clear toast."""
        self.toast_message = ""

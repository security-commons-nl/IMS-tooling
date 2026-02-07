"""
Admin State - handles admin panel data and actions
"""
import reflex as rx
from typing import Dict, Any, List

from ims.api.client import api_client


class AdminState(rx.State):
    """State for the admin panel."""

    active_tab: str = "overzicht"

    # Overview stats
    total_users: int = 0
    active_users: int = 0
    admin_users: int = 0
    inactive_users: int = 0

    # System health (flattened for Reflex compatibility)
    db_status: str = "unknown"
    ollama_status: str = "unknown"
    ollama_url: str = ""
    api_version: str = ""
    health_timestamp: str = ""

    # Audit log
    audit_entries: List[Dict[str, Any]] = []

    # Password management
    users_for_pw: List[Dict[str, Any]] = []

    # Password dialog
    show_pw_dialog: bool = False
    pw_target_user_id: int = 0
    pw_target_username: str = ""
    pw_new_password: str = ""
    pw_error: str = ""
    pw_success: str = ""

    # Loading states
    is_loading: bool = False

    async def load_all(self):
        """Load all admin panel data."""
        self.is_loading = True
        try:
            await self._load_stats()
            await self._load_health()
            self.audit_entries = await api_client.get_audit_log(limit=100)
            self.users_for_pw = await api_client.get_users(is_active=True, limit=200)
        except Exception:
            pass
        self.is_loading = False

    async def _load_stats(self):
        stats = await api_client.get_system_stats()
        self.total_users = stats.get("total_users", 0)
        self.active_users = stats.get("active_users", 0)
        self.admin_users = stats.get("admin_users", 0)
        self.inactive_users = stats.get("inactive_users", 0)

    async def _load_health(self):
        h = await api_client.get_system_health()
        self.db_status = h.get("database", {}).get("status", "unknown")
        self.ollama_status = h.get("ollama", {}).get("status", "unknown")
        self.ollama_url = h.get("ollama", {}).get("url", "")
        self.api_version = h.get("version", "")
        self.health_timestamp = h.get("timestamp", "")

    async def load_overview(self):
        """Load overview stats."""
        try:
            await self._load_stats()
        except Exception:
            pass

    async def load_health(self):
        """Load system health."""
        try:
            await self._load_health()
        except Exception:
            pass

    async def load_audit(self):
        """Load audit log."""
        try:
            self.audit_entries = await api_client.get_audit_log(limit=100)
        except Exception:
            pass

    async def load_users(self):
        """Load users for password management."""
        try:
            self.users_for_pw = await api_client.get_users(is_active=True, limit=200)
        except Exception:
            pass

    def open_pw_dialog(self, user_id: int, username: str):
        """Open password change dialog for a user."""
        self.pw_target_user_id = user_id
        self.pw_target_username = username
        self.pw_new_password = ""
        self.pw_error = ""
        self.pw_success = ""
        self.show_pw_dialog = True

    def close_pw_dialog(self):
        """Close password dialog."""
        self.show_pw_dialog = False
        self.pw_new_password = ""
        self.pw_error = ""

    def set_pw_new_password(self, value: str):
        self.pw_new_password = value

    async def change_user_password(self):
        """Change a user's password."""
        self.pw_error = ""
        self.pw_success = ""

        if len(self.pw_new_password) < 8:
            self.pw_error = "Wachtwoord moet minimaal 8 tekens zijn"
            return

        try:
            await api_client.change_password(
                user_id=self.pw_target_user_id,
                new_password=self.pw_new_password,
            )
            self.pw_success = f"Wachtwoord van {self.pw_target_username} is gewijzigd"
            self.pw_new_password = ""
        except Exception:
            self.pw_error = "Fout bij wijzigen van wachtwoord"

    def set_active_tab(self, tab: str):
        self.active_tab = tab

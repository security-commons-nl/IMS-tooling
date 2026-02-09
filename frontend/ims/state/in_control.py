"""
In-Control State — Hiaat 5
"""
import reflex as rx
from typing import List, Dict, Any
from ims.api.client import api_client
from ims.state.auth import AuthState


class InControlState(rx.State):
    """In-control dashboard state."""

    dashboard_items: List[Dict[str, Any]] = []
    is_loading: bool = False
    error: str = ""

    @rx.var
    def in_control_count(self) -> int:
        return len([i for i in self.dashboard_items if i.get("level") == "In control"])

    @rx.var
    def limited_count(self) -> int:
        return len([i for i in self.dashboard_items if i.get("level") == "Beperkt in control"])

    @rx.var
    def not_in_control_count(self) -> int:
        return len([i for i in self.dashboard_items if i.get("level") == "Niet in control"])

    async def load_dashboard(self):
        self.is_loading = True
        self.error = ""
        try:
            auth = await self.get_state(AuthState)
            tid = auth.tenant_id
            self.dashboard_items = await api_client.get_in_control_dashboard(tenant_id=tid)
        except Exception:
            self.dashboard_items = []
        finally:
            self.is_loading = False

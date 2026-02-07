"""
Dashboard State — aggregated dashboard data including ACT-overdue (Hiaat 7)
"""
import reflex as rx
from typing import Dict, Any
from ims.api.client import api_client


class DashboardState(rx.State):
    """Dashboard aggregation state."""

    act_overdue: Dict[str, Any] = {}

    @rx.var
    def blocked_count(self) -> int:
        return self.act_overdue.get("blocked_count", 0)

    @rx.var
    def no_action_count(self) -> int:
        return self.act_overdue.get("no_action_count", 0)

    @rx.var
    def open_findings_count(self) -> int:
        return self.act_overdue.get("open_findings_count", 0)

    @rx.var
    def has_act_warnings(self) -> bool:
        return (self.act_overdue.get("blocked_count", 0) + self.act_overdue.get("no_action_count", 0)) > 0

    async def load_dashboard_data(self):
        try:
            self.act_overdue = await api_client.get_act_overdue_summary(tenant_id=1)
        except Exception:
            self.act_overdue = {}

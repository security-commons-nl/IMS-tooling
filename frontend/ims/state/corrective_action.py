"""
Corrective Action State - handles verbeteracties management data
"""
import reflex as rx
from typing import List, Dict, Any, Optional
from ims.api.client import api_client
from ims.state.auth import AuthState


class CorrectiveActionState(rx.State):
    """Corrective actions (verbeteracties) management state."""

    items: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {}

    # Lookup data for dropdowns
    users: List[Dict[str, Any]] = []
    risks: List[Dict[str, Any]] = []
    controls: List[Dict[str, Any]] = []

    # Filters
    filter_status: str = "ALLE"
    filter_priority: str = "ALLE"
    filter_source: str = "ALLE"

    # Dialog state
    show_form_dialog: bool = False
    is_editing: bool = False
    editing_action_id: Optional[int] = None

    # Form fields
    form_title: str = ""
    form_description: str = ""
    form_action_type: str = "Corrective"
    form_priority: str = "MEDIUM"
    form_due_date: str = ""
    form_assigned_to_id: str = ""
    form_risk_id: str = ""
    form_control_id: str = ""
    form_finding_id: str = ""
    form_incident_id: str = ""

    # Delete confirmation
    show_delete_dialog: bool = False
    deleting_action_id: Optional[int] = None
    deleting_action_title: str = ""

    # Success/Error messages
    success_message: str = ""

    # Loading
    is_loading: bool = False
    error: str = ""

    # =========================================================================
    # COMPUTED VARS
    # =========================================================================

    @rx.var
    def total_count(self) -> int:
        return self.stats.get("total", 0) if self.stats else 0

    @rx.var
    def open_count(self) -> int:
        return self.stats.get("open", 0) if self.stats else 0

    @rx.var
    def overdue_count(self) -> int:
        return self.stats.get("overdue", 0) if self.stats else 0

    @rx.var
    def completed_count(self) -> int:
        return self.stats.get("completed", 0) if self.stats else 0

    @rx.var
    def verified_count(self) -> int:
        return self.stats.get("verified", 0) if self.stats else 0

    @rx.var
    def filtered_items(self) -> List[Dict[str, Any]]:
        """Client-side secondary filtering (main filtering via API)."""
        return self.items

    # =========================================================================
    # DATA LOADING
    # =========================================================================

    async def load_items(self):
        """Load corrective actions and stats from API."""
        self.is_loading = True
        self.error = ""
        self.success_message = ""

        try:
            # Map filter to API param
            status_param = None
            if self.filter_status == "OPEN":
                status_param = "open"
            elif self.filter_status == "ACHTERSTALLIG":
                status_param = "overdue"
            elif self.filter_status == "AFGEROND":
                status_param = "completed"
            elif self.filter_status == "GEVERIFIEERD":
                status_param = "verified"

            priority_param = None
            if self.filter_priority != "ALLE":
                priority_param = self.filter_priority

            source_param = None
            source_map = {
                "FINDING": "finding",
                "INCIDENT": "incident",
                "ISSUE": "issue",
                "INITIATIVE": "initiative",
                "RISK": "risk",
                "CONTROL": "control",
            }
            if self.filter_source != "ALLE":
                source_param = source_map.get(self.filter_source)

            self.items = await api_client.get_corrective_actions(
                status=status_param,
                priority=priority_param,
                source_type=source_param,
            )
            self.stats = await api_client.get_corrective_action_stats()
        except Exception as e:
            self.error = f"Kan verbeteracties niet laden: {str(e)}"
            self.items = []
            self.stats = {}
        finally:
            self.is_loading = False

    async def load_lookup_data(self):
        """Load users, risks, controls for dropdowns."""
        try:
            self.users = await api_client.get_users()
            self.risks = await api_client.get_risks(limit=500)
            self.controls = await api_client.get_controls(limit=500)
        except Exception:
            pass  # Graceful fallback

    async def load_all(self):
        """Load items + lookup data on page mount."""
        await self.load_items()
        await self.load_lookup_data()

    # =========================================================================
    # FILTERS
    # =========================================================================

    def set_filter_status(self, value: str):
        self.filter_status = value
        return CorrectiveActionState.load_items

    def set_filter_priority(self, value: str):
        self.filter_priority = value
        return CorrectiveActionState.load_items

    def set_filter_source(self, value: str):
        self.filter_source = value
        return CorrectiveActionState.load_items

    def clear_filters(self):
        self.filter_status = "ALLE"
        self.filter_priority = "ALLE"
        self.filter_source = "ALLE"
        return CorrectiveActionState.load_items

    # =========================================================================
    # FORM METHODS
    # =========================================================================

    def _reset_form(self):
        self.form_title = ""
        self.form_description = ""
        self.form_action_type = "Corrective"
        self.form_priority = "MEDIUM"
        self.form_due_date = ""
        self.form_assigned_to_id = ""
        self.form_risk_id = ""
        self.form_control_id = ""
        self.form_finding_id = ""
        self.form_incident_id = ""
        self.error = ""

    def open_create_dialog(self):
        self.is_editing = False
        self.editing_action_id = None
        self._reset_form()
        self.show_form_dialog = True

    def open_edit_dialog(self, action_id: int):
        for item in self.items:
            if item.get("id") == action_id:
                self.is_editing = True
                self.editing_action_id = action_id
                self.form_title = item.get("title", "")
                self.form_description = item.get("description", "") or ""
                self.form_action_type = item.get("action_type", "Corrective") or "Corrective"
                self.form_priority = item.get("priority", "MEDIUM") or "MEDIUM"
                self.form_due_date = (item.get("due_date", "") or "")[:10]
                self.form_assigned_to_id = str(item.get("assigned_to_id", "") or "")
                self.form_risk_id = str(item.get("risk_id", "") or "")
                self.form_control_id = str(item.get("control_id", "") or "")
                self.form_finding_id = str(item.get("finding_id", "") or "")
                self.form_incident_id = str(item.get("incident_id", "") or "")
                self.show_form_dialog = True
                break

    def close_form_dialog(self):
        self.show_form_dialog = False
        self._reset_form()

    # Form field setters
    def set_form_title(self, value: str):
        self.form_title = value

    def set_form_description(self, value: str):
        self.form_description = value

    def set_form_action_type(self, value: str):
        self.form_action_type = value

    def set_form_priority(self, value: str):
        self.form_priority = value

    def set_form_due_date(self, value: str):
        self.form_due_date = value

    def set_form_assigned_to_id(self, value: str):
        self.form_assigned_to_id = value

    def set_form_risk_id(self, value: str):
        self.form_risk_id = value

    def set_form_control_id(self, value: str):
        self.form_control_id = value

    def set_form_finding_id(self, value: str):
        self.form_finding_id = value

    def set_form_incident_id(self, value: str):
        self.form_incident_id = value

    # =========================================================================
    # CRUD METHODS
    # =========================================================================

    async def save_item(self):
        """Save corrective action (create or update)."""
        if not self.form_title.strip():
            self.error = "Titel is verplicht"
            return

        auth = await self.get_state(AuthState)
        tid = auth.tenant_id

        try:
            data = {
                "title": self.form_title.strip(),
                "description": self.form_description.strip() or None,
                "action_type": self.form_action_type,
                "priority": self.form_priority,
                "tenant_id": tid,
            }

            if self.form_due_date:
                data["due_date"] = self.form_due_date + "T00:00:00"
            if self.form_assigned_to_id:
                data["assigned_to_id"] = int(self.form_assigned_to_id)
            if self.form_risk_id:
                data["risk_id"] = int(self.form_risk_id)
            if self.form_control_id:
                data["control_id"] = int(self.form_control_id)
            if self.form_finding_id:
                data["finding_id"] = int(self.form_finding_id)
            if self.form_incident_id:
                data["incident_id"] = int(self.form_incident_id)

            if self.is_editing and self.editing_action_id:
                await api_client.update_standalone_corrective_action(
                    self.editing_action_id, data
                )
                self.success_message = "Verbeteractie bijgewerkt"
            else:
                await api_client.create_standalone_corrective_action(data)
                self.success_message = "Verbeteractie aangemaakt"

            self.show_form_dialog = False
            self._reset_form()
            await self.load_items()

        except Exception as e:
            self.error = f"Fout bij opslaan: {str(e)}"

    async def complete_action(self, action_id: int):
        """Mark action as completed."""
        try:
            await api_client.complete_standalone_corrective_action(action_id)
            self.success_message = "Actie afgerond"
            await self.load_items()
        except Exception as e:
            self.error = f"Fout bij afronden: {str(e)}"

    async def verify_action(self, action_id: int):
        """Verify a completed action."""
        auth = await self.get_state(AuthState)
        try:
            await api_client.verify_standalone_corrective_action(
                action_id, auth.user_id
            )
            self.success_message = "Actie geverifieerd"
            await self.load_items()
        except Exception as e:
            self.error = f"Fout bij verifiëren: {str(e)}"

    # =========================================================================
    # DELETE METHODS
    # =========================================================================

    def open_delete_dialog(self, action_id: int):
        for item in self.items:
            if item.get("id") == action_id:
                self.deleting_action_id = action_id
                self.deleting_action_title = item.get("title", "")
                self.show_delete_dialog = True
                break

    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.deleting_action_id = None
        self.deleting_action_title = ""

    async def confirm_delete(self):
        if not self.deleting_action_id:
            return
        try:
            await api_client.delete_standalone_corrective_action(
                self.deleting_action_id
            )
            self.success_message = "Verbeteractie verwijderd"
            self.close_delete_dialog()
            await self.load_items()
        except Exception as e:
            self.error = f"Fout bij verwijderen: {str(e)}"
            self.close_delete_dialog()

"""
Incident State - handles incident management data
"""
import reflex as rx
from typing import List, Dict, Any, Optional
from ims.api.client import api_client


class IncidentState(rx.State):
    """Incident management state."""

    incidents: List[Dict[str, Any]] = []
    selected_incident: Dict[str, Any] = {}

    # Filters
    filter_status: str = "ALLE"
    filter_data_breach: str = "ALLE"

    # Dialog state
    show_form_dialog: bool = False
    is_editing: bool = False
    editing_incident_id: Optional[int] = None

    # Form fields
    form_title: str = ""
    form_description: str = ""
    form_severity: str = "MEDIUM"
    form_status: str = "DRAFT"
    form_is_data_breach: bool = False
    
    # Delete confirmation
    show_delete_dialog: bool = False
    deleting_incident_id: Optional[int] = None
    deleting_incident_title: str = ""

    # Success/Error messages
    success_message: str = ""
    
    # Loading
    is_loading: bool = False
    error: str = ""

    @rx.var
    def open_count(self) -> int:
        return len([i for i in self.incidents if i.get("status") in ["DRAFT", "ACTIVE"]])

    @rx.var
    def data_breach_count(self) -> int:
        return len([i for i in self.incidents if i.get("is_data_breach")])

    @rx.var
    def overdue_breaches(self) -> List[Dict[str, Any]]:
        """Data breaches past notification deadline."""
        return [
            i for i in self.incidents
            if i.get("is_data_breach") and not i.get("notified_to_authority")
        ]

    async def load_incidents(self):
        """Load incidents from API."""
        self.is_loading = True
        self.error = ""

        try:
            params = {}
            if self.filter_status and self.filter_status != "ALLE":
                params["status"] = self.filter_status
            if self.filter_data_breach == "JA":
                params["is_data_breach"] = True
            elif self.filter_data_breach == "NEE":
                params["is_data_breach"] = False

            self.incidents = await api_client.get_incidents(**params)
        except Exception as e:
            self.error = f"Kan incidenten niet laden: {str(e)}"
            self.incidents = []
        finally:
            self.is_loading = False

    def set_filter_status(self, status: str):
        """Set status filter."""
        self.filter_status = status
        return IncidentState.load_incidents

    def set_filter_data_breach(self, value: str):
        """Set data breach filter."""
        self.filter_data_breach = value
        return IncidentState.load_incidents

    def clear_filters(self):
        """Clear all filters."""
        self.filter_status = "ALLE"
        self.filter_data_breach = "ALLE"
        return IncidentState.load_incidents

    # ==========================================================================
    # FORM METHODS
    # ==========================================================================

    def _reset_form(self):
        """Reset form fields."""
        self.form_title = ""
        self.form_description = ""
        self.form_severity = "MEDIUM"
        self.form_status = "DRAFT"
        self.form_is_data_breach = False
        self.error = ""

    def open_create_dialog(self):
        """Open dialog for creating a new incident."""
        self.is_editing = False
        self.editing_incident_id = None
        self._reset_form()
        self.show_form_dialog = True

    def open_edit_dialog(self, incident_id: int):
        """Open dialog for editing an existing incident."""
        for incident in self.incidents:
            if incident.get("id") == incident_id:
                self.is_editing = True
                self.editing_incident_id = incident_id
                self.form_title = incident.get("title", "")
                self.form_description = incident.get("description", "") or ""
                self.form_severity = incident.get("severity", "MEDIUM")
                self.form_status = incident.get("status", "DRAFT")
                self.form_is_data_breach = incident.get("is_data_breach", False)
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

    def set_form_severity(self, value: str):
        self.form_severity = value

    def set_form_status(self, value: str):
        self.form_status = value
        
    def set_form_is_data_breach(self, value: bool):
        self.form_is_data_breach = value

    # ==========================================================================
    # CRUD METHODS
    # ==========================================================================

    async def save_incident(self):
        """Save incident (create or update)."""
        if not self.form_title.strip():
            self.error = "Titel is verplicht"
            return
        if not self.form_description.strip():
            self.error = "Beschrijving is verplicht"
            return

        try:
            data = {
                "title": self.form_title.strip(),
                "description": self.form_description.strip(),
                "severity": self.form_severity,
                "status": self.form_status,
                "is_data_breach": self.form_is_data_breach,
                "tenant_id": 1,
            }

            if self.is_editing and self.editing_incident_id:
                await api_client.update_incident(self.editing_incident_id, data)
                self.success_message = "Incident bijgewerkt"
            else:
                await api_client.create_incident(data)
                self.success_message = "Incident gemeld"

            self.show_form_dialog = False
            self._reset_form()
            await self.load_incidents()

        except Exception as e:
            self.error = f"Fout bij opslaan: {str(e)}"

    # ==========================================================================
    # DELETE METHODS
    # ==========================================================================

    def open_delete_dialog(self, incident_id: int):
        """Open delete confirmation dialog."""
        for incident in self.incidents:
            if incident.get("id") == incident_id:
                self.deleting_incident_id = incident_id
                self.deleting_incident_title = incident.get("title", "")
                self.show_delete_dialog = True
                break

    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.deleting_incident_id = None
        self.deleting_incident_title = ""

    async def confirm_delete(self):
        """Confirm and execute delete."""
        if not self.deleting_incident_id:
            return

        try:
            await api_client.delete_incident(self.deleting_incident_id)
            self.success_message = "Incident verwijderd"
            self.close_delete_dialog()
            await self.load_incidents()
        except Exception as e:
            self.error = f"Fout bij verwijderen: {str(e)}"
            self.close_delete_dialog()

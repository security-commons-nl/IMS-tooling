"""
Measure State - handles control measures data
"""
import reflex as rx
from typing import List, Dict, Any, Optional
from ims.api.client import api_client
from ims.state.auth import AuthState


class MeasureState(rx.State):
    """Measure management state."""

    measures: List[Dict[str, Any]] = []
    selected_measure: Dict[str, Any] = {}

    # Loading
    is_loading: bool = False
    error: str = ""

    # Dialog state
    show_form_dialog: bool = False
    is_editing: bool = False
    editing_measure_id: Optional[int] = None

    # Form fields
    form_name: str = ""
    form_description: str = ""
    form_control_type: str = "Preventive"
    form_scope_id: str = ""

    # Delete confirmation
    show_delete_dialog: bool = False
    deleting_measure_id: Optional[int] = None
    deleting_measure_name: str = ""

    # Success/Error messages
    success_message: str = ""

    async def load_measures(self):
        """Load measures from API."""
        self.is_loading = True
        self.error = ""
        self.success_message = ""

        try:
            self.measures = await api_client.get_measures()
        except Exception as e:
            self.error = f"Kan maatregelen niet laden: {str(e)}"
            self.measures = []
        finally:
            self.is_loading = False

    # ==========================================================================
    # FORM METHODS
    # ==========================================================================

    def _reset_form(self):
        """Reset form fields."""
        self.form_name = ""
        self.form_description = ""
        self.form_control_type = "Preventive"
        self.form_scope_id = ""
        self.error = ""

    def open_create_dialog(self):
        """Open dialog for creating a new measure."""
        self.is_editing = False
        self.editing_measure_id = None
        self._reset_form()
        self.show_form_dialog = True

    def open_edit_dialog(self, measure_id: int):
        """Open dialog for editing an existing measure."""
        for measure in self.measures:
            if measure.get("id") == measure_id:
                self.is_editing = True
                self.editing_measure_id = measure_id
                self.form_name = measure.get("name", "")
                self.form_description = measure.get("description", "") or ""
                self.form_control_type = measure.get("control_type", "Preventive") or "Preventive"
                # Scope ID handling to be added whenever scope selection is implemented
                self.show_form_dialog = True
                break

    def close_form_dialog(self):
        self.show_form_dialog = False
        self._reset_form()

    # Form field setters
    def set_form_name(self, value: str):
        self.form_name = value

    def set_form_description(self, value: str):
        self.form_description = value

    def set_form_control_type(self, value: str):
        self.form_control_type = value

    # ==========================================================================
    # CRUD METHODS
    # ==========================================================================

    async def save_measure(self):
        """Save measure (create or update)."""
        if not self.form_name.strip():
            self.error = "Naam is verplicht"
            return
        if not self.form_description.strip():
            self.error = "Beschrijving is verplicht"
            return

        auth = await self.get_state(AuthState)
        tid = auth.tenant_id

        try:
            data = {
                "name": self.form_name.strip(),
                "description": self.form_description.strip(),
                "control_type": self.form_control_type,
                "tenant_id": tid,
            }

            if self.is_editing and self.editing_measure_id:
                await api_client.update_measure(self.editing_measure_id, data)
                self.success_message = "Maatregel bijgewerkt"
            else:
                await api_client.create_measure(data)
                self.success_message = "Maatregel aangemaakt"

            self.show_form_dialog = False
            self._reset_form()
            await self.load_measures()

        except Exception as e:
            self.error = f"Fout bij opslaan: {str(e)}"

    # ==========================================================================
    # DELETE METHODS
    # ==========================================================================

    def open_delete_dialog(self, measure_id: int):
        """Open delete confirmation dialog."""
        for measure in self.measures:
            if measure.get("id") == measure_id:
                self.deleting_measure_id = measure_id
                self.deleting_measure_name = measure.get("name", "")
                self.show_delete_dialog = True
                break

    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.deleting_measure_id = None
        self.deleting_measure_name = ""

    async def confirm_delete(self):
        """Confirm and execute delete."""
        if not self.deleting_measure_id:
            return

        try:
            await api_client.delete_measure(self.deleting_measure_id)
            self.success_message = "Maatregel verwijderd"
            self.close_delete_dialog()
            await self.load_measures()
        except Exception as e:
            self.error = f"Fout bij verwijderen: {str(e)}"
            self.close_delete_dialog()

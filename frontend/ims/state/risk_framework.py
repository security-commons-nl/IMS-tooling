"""
Risk Framework State — Risicokader (Hiaat 3)
"""
import json
import reflex as rx
from typing import List, Dict, Any, Optional
from ims.api.client import api_client
from ims.state.auth import AuthState


class RiskFrameworkState(rx.State):
    """Risk framework state."""

    frameworks: List[Dict[str, Any]] = []
    is_loading: bool = False
    error: str = ""
    success_message: str = ""

    show_form_dialog: bool = False
    is_editing: bool = False
    editing_id: Optional[int] = None

    form_name: str = ""
    form_impact_definitions: str = ""
    form_likelihood_definitions: str = ""
    form_risk_tolerance: str = ""
    form_decision_rules: str = ""

    show_delete_dialog: bool = False
    deleting_id: Optional[int] = None

    async def load_frameworks(self):
        self.is_loading = True
        self.error = ""
        self.success_message = ""
        try:
            self.frameworks = await api_client.get_risk_frameworks()
        except Exception as e:
            self.error = f"Fout bij laden frameworks: {str(e)}"
            self.frameworks = []
        finally:
            self.is_loading = False

    def open_create_dialog(self):
        self.is_editing = False
        self.editing_id = None
        self._reset_form()
        self.show_form_dialog = True

    async def open_edit_dialog(self, framework_id: int):
        for fw in self.frameworks:
            if fw.get("id") == framework_id:
                self.is_editing = True
                self.editing_id = framework_id
                self.form_name = fw.get("name", "")
                self.form_impact_definitions = self._to_str(fw.get("impact_definitions", ""))
                self.form_likelihood_definitions = self._to_str(fw.get("likelihood_definitions", ""))
                self.form_risk_tolerance = self._to_str(fw.get("risk_tolerance", ""))
                self.form_decision_rules = self._to_str(fw.get("decision_rules", ""))
                self.show_form_dialog = True
                break

    def close_form_dialog(self):
        self.show_form_dialog = False
        self._reset_form()

    def _reset_form(self):
        self.form_name = ""
        self.form_impact_definitions = ""
        self.form_likelihood_definitions = ""
        self.form_risk_tolerance = ""
        self.form_decision_rules = ""
        self.error = ""
        self.success_message = ""

    @staticmethod
    def _to_str(value) -> str:
        """Convert value to string, handling dicts/lists from JSON API responses."""
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    def set_form_name(self, v: str): self.form_name = v
    def set_form_impact_definitions(self, v: str): self.form_impact_definitions = v
    def set_form_likelihood_definitions(self, v: str): self.form_likelihood_definitions = v
    def set_form_risk_tolerance(self, v: str): self.form_risk_tolerance = v
    def set_form_decision_rules(self, v: str): self.form_decision_rules = v

    async def save_framework(self):
        self.error = ""
        if not self.form_name.strip():
            self.error = "Naam is verplicht"
            return

        auth = await self.get_state(AuthState)
        tid = auth.tenant_id

        data = {
            "name": self.form_name.strip(),
            "impact_definitions": self.form_impact_definitions or "{}",
            "likelihood_definitions": self.form_likelihood_definitions or "{}",
            "risk_tolerance": self.form_risk_tolerance or "{}",
            "decision_rules": self.form_decision_rules or "{}",
            "tenant_id": tid,
        }

        try:
            if self.is_editing and self.editing_id:
                await api_client.update_risk_framework(self.editing_id, data)
                self.success_message = "Risicokader bijgewerkt"
            else:
                await api_client.create_risk_framework(data)
                self.success_message = "Risicokader aangemaakt"

            self.show_form_dialog = False
            self._reset_form()
            return RiskFrameworkState.load_frameworks
        except Exception as e:
            self.error = f"Fout bij opslaan: {str(e)}"

    def open_delete_dialog(self, framework_id: int):
        self.deleting_id = framework_id
        self.show_delete_dialog = True

    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.deleting_id = None

    async def confirm_delete(self):
        if not self.deleting_id:
            return
        try:
            async with api_client._get_client() as client:
                response = await client.delete(f"/risk-framework/{self.deleting_id}")
                response.raise_for_status()
            self.success_message = "Risicokader verwijderd"
            self.show_delete_dialog = False
            self.deleting_id = None
            return RiskFrameworkState.load_frameworks
        except Exception as e:
            self.error = f"Fout bij verwijderen: {str(e)}"
            self.show_delete_dialog = False

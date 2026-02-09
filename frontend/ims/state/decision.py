"""
Decision State — Besluitlog (Hiaat 1)
"""
import reflex as rx
from typing import List, Dict, Any, Optional
from ims.api.client import api_client
from ims.state.auth import AuthState


class DecisionState(rx.State):
    """Decision log state."""

    decisions: List[Dict[str, Any]] = []
    is_loading: bool = False
    error: str = ""
    success_message: str = ""

    # Dialog
    show_form_dialog: bool = False
    is_editing: bool = False
    editing_id: Optional[int] = None

    # Form fields
    form_decision_type: str = "Restrisico-acceptatie"
    form_decision_text: str = ""
    form_decision_maker_id: str = "1"
    form_valid_until: str = ""
    form_justification: str = ""
    form_scope_id: str = ""

    # Delete
    show_delete_dialog: bool = False
    deleting_id: Optional[int] = None
    deleting_title: str = ""

    # Linked risks
    linked_risks: List[Dict[str, Any]] = []

    async def load_decisions(self):
        self.is_loading = True
        self.error = ""
        self.success_message = ""
        try:
            self.decisions = await api_client.get_decisions()
        except Exception as e:
            self.error = f"Fout bij laden besluiten: {str(e)}"
            self.decisions = []
        finally:
            self.is_loading = False

    def open_create_dialog(self):
        self.is_editing = False
        self.editing_id = None
        self._reset_form()
        self.show_form_dialog = True

    async def open_edit_dialog(self, decision_id: int):
        for d in self.decisions:
            if d.get("id") == decision_id:
                self.is_editing = True
                self.editing_id = decision_id
                self.form_decision_type = d.get("decision_type", "")
                self.form_decision_text = d.get("decision_text", "")
                self.form_decision_maker_id = str(d.get("decision_maker_id", "1"))
                self.form_justification = d.get("justification", "") or ""
                self.form_scope_id = str(d.get("scope_id", "")) if d.get("scope_id") else ""
                self.show_form_dialog = True
                break

    def close_form_dialog(self):
        self.show_form_dialog = False
        self._reset_form()

    def _reset_form(self):
        self.form_decision_type = "Restrisico-acceptatie"
        self.form_decision_text = ""
        self.form_decision_maker_id = "1"
        self.form_valid_until = ""
        self.form_justification = ""
        self.form_scope_id = ""
        self.error = ""
        self.success_message = ""

    # Setters
    def set_form_decision_type(self, v: str): self.form_decision_type = v
    def set_form_decision_text(self, v: str): self.form_decision_text = v
    def set_form_decision_maker_id(self, v: str): self.form_decision_maker_id = v
    def set_form_valid_until(self, v: str): self.form_valid_until = v
    def set_form_justification(self, v: str): self.form_justification = v
    def set_form_scope_id(self, v: str): self.form_scope_id = v

    async def save_decision(self):
        self.error = ""
        if not self.form_decision_text.strip():
            self.error = "Besluittekst is verplicht"
            return

        auth = await self.get_state(AuthState)
        tid = auth.tenant_id

        data = {
            "decision_type": self.form_decision_type,
            "decision_text": self.form_decision_text.strip(),
            "decision_maker_id": int(self.form_decision_maker_id) if self.form_decision_maker_id else 1,
            "tenant_id": tid,
        }
        if self.form_justification:
            data["justification"] = self.form_justification
        if self.form_valid_until:
            data["valid_until"] = self.form_valid_until
        if self.form_scope_id:
            data["scope_id"] = int(self.form_scope_id)

        try:
            if self.is_editing and self.editing_id:
                await api_client.update_decision(self.editing_id, data)
                self.success_message = "Besluit bijgewerkt"
            else:
                await api_client.create_decision(data)
                self.success_message = "Besluit aangemaakt"

            self.show_form_dialog = False
            self._reset_form()
            return DecisionState.load_decisions
        except Exception as e:
            self.error = f"Fout bij opslaan: {str(e)}"

    def open_delete_dialog(self, decision_id: int):
        for d in self.decisions:
            if d.get("id") == decision_id:
                self.deleting_id = decision_id
                self.deleting_title = d.get("decision_text", "")[:60]
                self.show_delete_dialog = True
                break

    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.deleting_id = None
        self.deleting_title = ""

    async def confirm_delete(self):
        if not self.deleting_id:
            return
        try:
            await api_client.delete_decision(self.deleting_id)
            self.success_message = "Besluit verwijderd"
            self.show_delete_dialog = False
            self.deleting_id = None
            return DecisionState.load_decisions
        except Exception as e:
            self.error = f"Fout bij verwijderen: {str(e)}"
            self.show_delete_dialog = False

"""
Policy Principle State — Beleid-trace (Hiaat 6)
"""
import reflex as rx
from typing import List, Dict, Any, Optional
from ims.api.client import api_client
from ims.state.auth import AuthState


class PolicyPrincipleState(rx.State):
    """Policy principle management state."""

    principles: List[Dict[str, Any]] = []
    policies: List[Dict[str, Any]] = []
    is_loading: bool = False
    error: str = ""
    success_message: str = ""

    # Dialog
    show_form_dialog: bool = False
    is_editing: bool = False
    editing_id: Optional[int] = None

    # Form fields
    form_code: str = ""
    form_title: str = ""
    form_description: str = ""
    form_policy_id: str = ""

    # Delete
    show_delete_dialog: bool = False
    deleting_id: Optional[int] = None
    deleting_title: str = ""

    # Trace
    show_trace_dialog: bool = False
    trace_data: Dict[str, Any] = {}

    async def load_principles(self):
        self.is_loading = True
        self.error = ""
        self.success_message = ""
        try:
            self.principles = await api_client.get_policy_principles()
            self.policies = await api_client.get_policies()
        except Exception as e:
            self.error = f"Fout bij laden principes: {str(e)}"
            self.principles = []
        finally:
            self.is_loading = False

    def open_create_dialog(self):
        self.is_editing = False
        self.editing_id = None
        self._reset_form()
        self.show_form_dialog = True

    async def open_edit_dialog(self, principle_id: int):
        for p in self.principles:
            if p.get("id") == principle_id:
                self.is_editing = True
                self.editing_id = principle_id
                self.form_code = p.get("code", "")
                self.form_title = p.get("title", "")
                self.form_description = p.get("description", "") or ""
                self.form_policy_id = str(p.get("policy_id", ""))
                self.show_form_dialog = True
                break

    def close_form_dialog(self):
        self.show_form_dialog = False
        self._reset_form()

    def _reset_form(self):
        self.form_code = ""
        self.form_title = ""
        self.form_description = ""
        self.form_policy_id = ""
        self.error = ""
        self.success_message = ""

    # Setters
    def set_form_code(self, v: str): self.form_code = v
    def set_form_title(self, v: str): self.form_title = v
    def set_form_description(self, v: str): self.form_description = v
    def set_form_policy_id(self, v: str): self.form_policy_id = v

    async def save_principle(self):
        self.error = ""
        if not self.form_code.strip():
            self.error = "Code is verplicht"
            return
        if not self.form_title.strip():
            self.error = "Titel is verplicht"
            return
        if not self.form_policy_id:
            self.error = "Beleid is verplicht"
            return

        auth = await self.get_state(AuthState)
        tid = auth.tenant_id

        data = {
            "code": self.form_code.strip(),
            "title": self.form_title.strip(),
            "description": self.form_description or None,
            "policy_id": int(self.form_policy_id),
            "tenant_id": tid,
        }

        try:
            if self.is_editing and self.editing_id:
                async with api_client._get_client() as client:
                    response = await client.patch(f"/policy-principles/{self.editing_id}", json=data)
                    response.raise_for_status()
                self.success_message = "Uitgangspunt bijgewerkt"
            else:
                await api_client.create_policy_principle(data)
                self.success_message = "Uitgangspunt aangemaakt"

            self.show_form_dialog = False
            self._reset_form()
            return PolicyPrincipleState.load_principles
        except Exception as e:
            self.error = f"Fout bij opslaan: {str(e)}"

    def open_delete_dialog(self, principle_id: int):
        for p in self.principles:
            if p.get("id") == principle_id:
                self.deleting_id = principle_id
                self.deleting_title = p.get("title", "")[:60]
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
            async with api_client._get_client() as client:
                response = await client.delete(f"/policy-principles/{self.deleting_id}")
                response.raise_for_status()
            self.success_message = "Uitgangspunt verwijderd"
            self.show_delete_dialog = False
            self.deleting_id = None
            return PolicyPrincipleState.load_principles
        except Exception as e:
            self.error = f"Fout bij verwijderen: {str(e)}"
            self.show_delete_dialog = False

    async def show_trace(self, control_id: int):
        try:
            self.trace_data = await api_client.get_control_trace(control_id)
            self.show_trace_dialog = True
        except Exception as e:
            self.error = f"Fout bij laden trace: {str(e)}"

    def close_trace_dialog(self):
        self.show_trace_dialog = False
        self.trace_data = {}

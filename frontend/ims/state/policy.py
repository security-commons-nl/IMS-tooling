"""
Policy State - handles policy management data
"""
import reflex as rx
from typing import List, Dict, Any, Optional
from ims.api.client import api_client
from ims.components.deadline import enrich_with_multiple_deadlines


class PolicyState(rx.State):
    """Policy management state."""

    policies: List[Dict[str, Any]] = []
    selected_policy: Dict[str, Any] = {}

    # Filters
    filter_state: str = "ALLE"

    # Dialog state
    show_form_dialog: bool = False
    is_editing: bool = False
    editing_policy_id: Optional[int] = None
    
    # Form fields
    form_title: str = ""
    form_content: str = ""
    form_version: str = "1.0"
    form_state: str = "Draft"
    
    # Delete confirmation
    show_delete_dialog: bool = False
    deleting_policy_id: Optional[int] = None
    deleting_policy_title: str = ""

    # Success/Error messages
    success_message: str = ""
    
    # Loading
    is_loading: bool = False
    error: str = ""

    # ==========================================================================
    # COMPUTED VARS - Counts by workflow state
    # ==========================================================================

    @rx.var
    def draft_count(self) -> int:
        return len([p for p in self.policies if p.get("state") == "Draft"])

    @rx.var
    def review_count(self) -> int:
        return len([p for p in self.policies if p.get("state") == "Review"])

    @rx.var
    def published_count(self) -> int:
        return len([p for p in self.policies if p.get("state") == "Published"])

    # ==========================================================================
    # COMPUTED VARS - Deadline status counts
    # ==========================================================================

    @rx.var
    def danger_count(self) -> int:
        """Count of policies with overdue deadlines."""
        return len([p for p in self.policies if p.get("_deadline_status") == "danger"])

    @rx.var
    def warning_count(self) -> int:
        """Count of policies with approaching deadlines."""
        return len([p for p in self.policies if p.get("_deadline_status") == "warning"])

    @rx.var
    def action_required_count(self) -> int:
        """Total items requiring attention (danger + warning)."""
        return self.danger_count + self.warning_count

    # ==========================================================================
    # DATA LOADING
    # ==========================================================================

    async def load_policies(self):
        """Load policies from API."""
        self.is_loading = True
        self.error = ""
        self.success_message = ""

        try:
            params = {}
            if self.filter_state and self.filter_state != "ALLE":
                params["state"] = self.filter_state

            policies = await api_client.get_policies(**params)

            # Enrich with deadline status (checks both review_date and expiration_date)
            self.policies = enrich_with_multiple_deadlines(
                policies,
                deadline_fields=["review_date", "expiration_date"]
            )
        except Exception as e:
            self.error = f"Kan beleid niet laden: {str(e)}"
            self.policies = []
        finally:
            self.is_loading = False

    # ==========================================================================
    # FORM METHODS
    # ==========================================================================

    def _reset_form(self):
        """Reset form fields."""
        self.form_title = ""
        self.form_content = ""
        self.form_version = "1.0"
        self.form_state = "Draft"
        self.error = ""

    def open_create_dialog(self):
        """Open dialog for creating a new policy."""
        self.is_editing = False
        self.editing_policy_id = None
        self._reset_form()
        self.show_form_dialog = True

    def open_edit_dialog(self, policy_id: int):
        """Open dialog for editing an existing policy."""
        for policy in self.policies:
            if policy.get("id") == policy_id:
                self.is_editing = True
                self.editing_policy_id = policy_id
                self.form_title = policy.get("title", "")
                self.form_content = policy.get("content", "") or ""
                self.form_version = policy.get("version", "1.0")
                self.form_state = policy.get("state", "Draft")
                self.show_form_dialog = True
                break

    def close_form_dialog(self):
        self.show_form_dialog = False
        self._reset_form()

    # Form field setters
    def set_form_title(self, value: str):
        self.form_title = value

    def set_form_content(self, value: str):
        self.form_content = value

    def set_form_version(self, value: str):
        self.form_version = value

    def set_form_state(self, value: str):
        self.form_state = value

    # ==========================================================================
    # CRUD METHODS
    # ==========================================================================

    async def save_policy(self):
        """Save policy (create or update)."""
        if not self.form_title.strip():
            self.error = "Titel is verplicht"
            return
        if not self.form_content.strip():
            self.error = "Inhoud is verplicht"
            return

        try:
            data = {
                "title": self.form_title.strip(),
                "content": self.form_content.strip(),
                "version": self.form_version.strip(),
                "state": self.form_state,
                "tenant_id": 1,
            }

            if self.is_editing and self.editing_policy_id:
                await api_client.update_policy(self.editing_policy_id, data)
                self.success_message = "Beleid bijgewerkt"
            else:
                await api_client.create_policy(data)
                self.success_message = "Beleid aangemaakt"

            self.show_form_dialog = False
            self._reset_form()
            await self.load_policies()

        except Exception as e:
            self.error = f"Fout bij opslaan: {str(e)}"

    # ==========================================================================
    # DELETE METHODS
    # ==========================================================================

    def open_delete_dialog(self, policy_id: int):
        """Open delete confirmation dialog."""
        for policy in self.policies:
            if policy.get("id") == policy_id:
                self.deleting_policy_id = policy_id
                self.deleting_policy_title = policy.get("title", "")
                self.show_delete_dialog = True
                break

    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.deleting_policy_id = None
        self.deleting_policy_title = ""

    async def confirm_delete(self):
        """Confirm and execute delete."""
        if not self.deleting_policy_id:
            return

        try:
            await api_client.delete_policy(self.deleting_policy_id)
            self.success_message = "Beleid verwijderd"
            self.close_delete_dialog()
            await self.load_policies()
        except Exception as e:
            self.error = f"Fout bij verwijderen: {str(e)}"
            self.close_delete_dialog()

    # ==========================================================================
    # FILTERS
    # ==========================================================================

    def set_filter_state(self, state: str):
        """Set state filter."""
        self.filter_state = state
        return PolicyState.load_policies

    def clear_filters(self):
        """Clear all filters."""
        self.filter_state = "ALLE"
        return PolicyState.load_policies

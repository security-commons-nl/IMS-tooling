"""
User State - handles user management data
"""
import reflex as rx
from typing import List, Dict, Any, Optional
from ims.api.client import api_client


class UserState(rx.State):
    """User management state."""

    users: List[Dict[str, Any]] = []
    scopes: List[Dict[str, Any]] = []  # Available scopes for role assignment
    selected_user: Dict[str, Any] = {}
    selected_user_scopes: List[Dict[str, Any]] = []  # User's assigned scopes/roles

    # Filters
    filter_active: str = "ACTIEF"  # ACTIEF, INACTIEF, ALLE

    # Dialog state
    show_form_dialog: bool = False
    is_editing: bool = False
    editing_user_id: Optional[int] = None

    # Role assignment dialog
    show_role_dialog: bool = False
    role_dialog_user_id: Optional[int] = None
    role_dialog_user_name: str = ""

    # Form fields
    form_username: str = ""
    form_email: str = ""
    form_full_name: str = ""
    form_phone: str = ""
    form_department: str = ""
    form_job_title: str = ""
    form_is_active: bool = True
    form_is_superuser: bool = False
    form_theme: str = "SYSTEM"
    form_language: str = "NL"

    # Role assignment form
    form_scope_id: str = ""
    form_role: str = ""

    # Delete confirmation
    show_delete_dialog: bool = False
    deleting_user_id: Optional[int] = None
    deleting_user_name: str = ""

    # Success/Error messages
    success_message: str = ""

    # Loading
    is_loading: bool = False
    error: str = ""

    @rx.var
    def active_count(self) -> int:
        return len([u for u in self.users if u.get("is_active", True)])

    @rx.var
    def inactive_count(self) -> int:
        return len([u for u in self.users if not u.get("is_active", True)])

    @rx.var
    def admin_count(self) -> int:
        return len([u for u in self.users if u.get("is_superuser", False)])

    async def load_users(self):
        """Load users from API."""
        self.is_loading = True
        self.error = ""
        self.success_message = ""

        try:
            is_active = True
            if self.filter_active == "INACTIEF":
                is_active = False
            elif self.filter_active == "ALLE":
                # Load both active and inactive
                active_users = await api_client.get_users(is_active=True)
                inactive_users = await api_client.get_users(is_active=False)
                self.users = active_users + inactive_users
                self.is_loading = False
                return

            self.users = await api_client.get_users(is_active=is_active)
        except Exception as e:
            self.error = f"Kan gebruikers niet laden: {str(e)}"
            self.users = []
        finally:
            self.is_loading = False

    async def load_scopes(self):
        """Load available scopes for role assignment."""
        try:
            self.scopes = await api_client.get_scopes()
        except Exception as e:
            self.error = f"Kan scopes niet laden: {str(e)}"
            self.scopes = []

    def set_filter_active(self, value: str):
        """Set active filter."""
        self.filter_active = value
        return UserState.load_users

    def clear_filters(self):
        """Clear all filters."""
        self.filter_active = "ACTIEF"
        return UserState.load_users

    # ==========================================================================
    # FORM METHODS
    # ==========================================================================

    def _reset_form(self):
        """Reset form fields."""
        self.form_username = ""
        self.form_email = ""
        self.form_full_name = ""
        self.form_phone = ""
        self.form_department = ""
        self.form_job_title = ""
        self.form_is_active = True
        self.form_is_superuser = False
        self.form_theme = "SYSTEM"
        self.form_language = "NL"
        self.error = ""

    def open_create_dialog(self):
        """Open dialog for creating a new user."""
        self.is_editing = False
        self.editing_user_id = None
        self._reset_form()
        self.show_form_dialog = True

    def open_edit_dialog(self, user_id: int):
        """Open dialog for editing an existing user."""
        for user in self.users:
            if user.get("id") == user_id:
                self.is_editing = True
                self.editing_user_id = user_id
                self.form_username = user.get("username", "")
                self.form_email = user.get("email", "")
                self.form_full_name = user.get("full_name", "") or ""
                self.form_phone = user.get("phone", "") or ""
                self.form_department = user.get("department", "") or ""
                self.form_job_title = user.get("job_title", "") or ""
                self.form_is_active = user.get("is_active", True)
                self.form_is_superuser = user.get("is_superuser", False)
                self.form_theme = user.get("theme", "SYSTEM") or "SYSTEM"
                self.form_language = user.get("preferred_language", "NL") or "NL"
                self.show_form_dialog = True
                break

    def close_form_dialog(self):
        self.show_form_dialog = False
        self._reset_form()

    # Form field setters
    def set_form_username(self, value: str):
        self.form_username = value

    def set_form_email(self, value: str):
        self.form_email = value

    def set_form_full_name(self, value: str):
        self.form_full_name = value

    def set_form_phone(self, value: str):
        self.form_phone = value

    def set_form_department(self, value: str):
        self.form_department = value

    def set_form_job_title(self, value: str):
        self.form_job_title = value

    def set_form_is_active(self, value: bool):
        self.form_is_active = value

    def set_form_is_superuser(self, value: bool):
        self.form_is_superuser = value

    def set_form_theme(self, value: str):
        self.form_theme = value

    def set_form_language(self, value: str):
        self.form_language = value

    # ==========================================================================
    # ROLE ASSIGNMENT METHODS
    # ==========================================================================

    async def open_role_dialog(self, user_id: int):
        """Open role assignment dialog for a user."""
        for user in self.users:
            if user.get("id") == user_id:
                self.role_dialog_user_id = user_id
                self.role_dialog_user_name = user.get("full_name") or user.get("username", "")
                self.form_scope_id = ""
                self.form_role = ""
                self.error = ""

                # Load scopes and user's current scope assignments
                await self.load_scopes()
                try:
                    self.selected_user_scopes = await api_client.get_user_scopes(user_id)
                except Exception as e:
                    self.selected_user_scopes = []
                    self.error = f"Kan rollen niet laden: {str(e)}"

                self.show_role_dialog = True
                break

    def close_role_dialog(self):
        self.show_role_dialog = False
        self.role_dialog_user_id = None
        self.role_dialog_user_name = ""
        self.selected_user_scopes = []
        self.form_scope_id = ""
        self.form_role = ""

    def set_form_scope_id(self, value: str):
        self.form_scope_id = value

    def set_form_role(self, value: str):
        self.form_role = value

    async def assign_role(self):
        """Assign a role to the user for selected scope."""
        if not self.form_scope_id or not self.form_role:
            self.error = "Selecteer een scope en rol"
            return

        if not self.role_dialog_user_id:
            return

        try:
            await api_client.assign_user_scope_role(
                user_id=self.role_dialog_user_id,
                scope_id=int(self.form_scope_id),
                role=self.form_role,
                tenant_id=1,  # Default tenant
            )
            self.success_message = "Rol toegewezen"
            self.form_scope_id = ""
            self.form_role = ""
            # Reload user's scopes
            self.selected_user_scopes = await api_client.get_user_scopes(self.role_dialog_user_id)
        except Exception as e:
            self.error = f"Fout bij toewijzen rol: {str(e)}"

    async def remove_role(self, scope_id: int, role: str):
        """Remove a role from the user for a scope."""
        if not self.role_dialog_user_id:
            return

        try:
            await api_client.remove_user_scope_role(
                user_id=self.role_dialog_user_id,
                scope_id=scope_id,
                role=role,
            )
            self.success_message = "Rol verwijderd"
            # Reload user's scopes
            self.selected_user_scopes = await api_client.get_user_scopes(self.role_dialog_user_id)
        except Exception as e:
            self.error = f"Fout bij verwijderen rol: {str(e)}"

    # ==========================================================================
    # CRUD METHODS
    # ==========================================================================

    async def save_user(self):
        """Save user (create or update)."""
        if not self.form_username.strip():
            self.error = "Gebruikersnaam is verplicht"
            return
        if not self.form_email.strip():
            self.error = "E-mail is verplicht"
            return

        try:
            data = {
                "username": self.form_username.strip(),
                "email": self.form_email.strip(),
                "full_name": self.form_full_name.strip() or None,
                "phone": self.form_phone.strip() or None,
                "department": self.form_department.strip() or None,
                "job_title": self.form_job_title.strip() or None,
                "is_active": self.form_is_active,
                "is_superuser": self.form_is_superuser,
                "theme": self.form_theme,
                "preferred_language": self.form_language,
            }

            if self.is_editing and self.editing_user_id:
                await api_client.update_user(self.editing_user_id, data)
                self.success_message = "Gebruiker bijgewerkt"
            else:
                await api_client.create_user(data)
                self.success_message = "Gebruiker aangemaakt"

            self.show_form_dialog = False
            self._reset_form()
            await self.load_users()

        except Exception as e:
            self.error = f"Fout bij opslaan: {str(e)}"

    # ==========================================================================
    # DELETE METHODS
    # ==========================================================================

    def open_delete_dialog(self, user_id: int):
        """Open delete confirmation dialog."""
        for user in self.users:
            if user.get("id") == user_id:
                self.deleting_user_id = user_id
                self.deleting_user_name = user.get("full_name") or user.get("username", "")
                self.show_delete_dialog = True
                break

    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.deleting_user_id = None
        self.deleting_user_name = ""

    async def confirm_delete(self):
        """Confirm and execute deactivation."""
        if not self.deleting_user_id:
            return

        try:
            await api_client.deactivate_user(self.deleting_user_id)
            self.success_message = "Gebruiker gedeactiveerd"
            self.close_delete_dialog()
            await self.load_users()
        except Exception as e:
            self.error = f"Fout bij deactiveren: {str(e)}"
            self.close_delete_dialog()

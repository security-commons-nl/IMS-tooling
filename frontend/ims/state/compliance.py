"""
Compliance State - Statement of Applicability (SoA) Management
"""
import reflex as rx
from typing import List, Dict, Any, Optional
from ims.api.client import api_client
from ims.state.auth import AuthState


class ComplianceState(rx.State):
    """State for compliance/SoA management."""

    # Data
    soa_entries: List[Dict[str, Any]] = []
    soa_summary: Dict[str, Any] = {}
    gaps: List[Dict[str, Any]] = []
    scopes: List[Dict[str, Any]] = []
    standards: List[Dict[str, Any]] = []

    # UI State
    is_loading: bool = False
    error: str = ""
    success_message: str = ""

    # Filters
    selected_scope_id: Optional[int] = None
    selected_standard_id: Optional[int] = None
    filter_coverage: str = "ALL"
    filter_status: str = "ALL"

    # Form state for editing
    show_edit_dialog: bool = False
    editing_entry: Dict[str, Any] = {}
    # Flattened edit fields (Reflex can't track nested dict mutations)
    edit_entry_id: int = 0
    edit_is_applicable: bool = True
    edit_implementation_status: str = ""
    edit_justification: str = ""
    edit_implementation_notes: str = ""

    # Initialize dialog
    show_init_dialog: bool = False

    # Wizard state (separate from page filters)
    init_scope_id: Optional[int] = None
    init_standard_id: Optional[int] = None
    init_requirement_count: int = 0
    init_is_loading: bool = False
    init_error: str = ""
    init_success: str = ""

    @rx.var
    def compliance_percentage(self) -> int:
        """Calculate compliance percentage from summary (as int for progress bar)."""
        if self.soa_summary:
            return int(self.soa_summary.get("compliance_percentage", 0))
        return 0

    @rx.var
    def compliance_percentage_display(self) -> str:
        """Compliance percentage formatted for display."""
        if self.soa_summary:
            pct = self.soa_summary.get("compliance_percentage", 0)
            return f"{pct:.1f}"
        return "0"

    @rx.var
    def total_requirements(self) -> int:
        """Get total requirements count."""
        if self.soa_summary:
            return self.soa_summary.get("total_requirements", 0)
        return len(self.soa_entries)

    @rx.var
    def implemented_count(self) -> int:
        """Get implemented count."""
        if self.soa_summary and "implementation" in self.soa_summary:
            return self.soa_summary["implementation"].get("implemented", 0)
        return 0

    @rx.var
    def in_progress_count(self) -> int:
        """Get in-progress count."""
        if self.soa_summary and "implementation" in self.soa_summary:
            return self.soa_summary["implementation"].get("in_progress", 0)
        return 0

    @rx.var
    def gaps_count(self) -> int:
        """Get gaps count."""
        return len(self.gaps)

    @rx.var
    def init_can_submit(self) -> bool:
        """Whether the wizard has both scope and standard selected."""
        return bool(self.init_scope_id) and bool(self.init_standard_id)

    @rx.var
    def filtered_entries(self) -> List[Dict[str, Any]]:
        """Get filtered SoA entries."""
        entries = self.soa_entries

        if self.filter_coverage != "ALL":
            entries = [e for e in entries if e.get("coverage_type") == self.filter_coverage]

        if self.filter_status != "ALL":
            entries = [e for e in entries if e.get("implementation_status") == self.filter_status]

        return entries

    async def load_scopes(self):
        """Load available scopes."""
        try:
            self.scopes = await api_client.get_scopes(limit=200)
        except Exception as e:
            print(f"Error loading scopes: {e}")

    async def load_standards(self):
        """Load available standards."""
        try:
            self.standards = await api_client.get_standards(limit=100)
        except Exception as e:
            print(f"Error loading standards: {e}")

    async def load_data(self):
        """Load all compliance data."""
        self.is_loading = True
        self.error = ""

        try:
            # Load scopes and standards first
            await self.load_scopes()
            await self.load_standards()

            # Load SoA entries
            params = {}
            if self.selected_scope_id:
                params["scope_id"] = self.selected_scope_id
            if self.selected_standard_id:
                params["standard_id"] = self.selected_standard_id

            self.soa_entries = await api_client.get_soa_entries(**params)

            # Load summary if scope is selected
            if self.selected_scope_id:
                self.soa_summary = await api_client.get_soa_summary(
                    scope_id=self.selected_scope_id,
                    standard_id=self.selected_standard_id,
                )
                self.gaps = await api_client.get_soa_gaps(
                    scope_id=self.selected_scope_id,
                )
            else:
                self.soa_summary = {}
                self.gaps = []

        except Exception as e:
            self.error = f"Fout bij laden: {str(e)}"
        finally:
            self.is_loading = False

    def set_selected_scope(self, scope_id: str):
        """Set selected scope and reload."""
        if scope_id and scope_id != "NONE":
            self.selected_scope_id = int(scope_id)
        else:
            self.selected_scope_id = None
        return ComplianceState.load_data

    def set_selected_standard(self, standard_id: str):
        """Set selected standard and reload."""
        if standard_id and standard_id != "NONE":
            self.selected_standard_id = int(standard_id)
        else:
            self.selected_standard_id = None
        return ComplianceState.load_data

    def set_filter_coverage(self, coverage: str):
        """Set coverage filter."""
        self.filter_coverage = coverage

    def set_filter_status(self, status: str):
        """Set status filter."""
        self.filter_status = status

    def clear_filters(self):
        """Clear all filters."""
        self.filter_coverage = "ALL"
        self.filter_status = "ALL"

    # Edit dialog
    def open_edit_dialog(self, entry_id: int):
        """Open edit dialog for an entry."""
        for entry in self.soa_entries:
            if entry.get("id") == entry_id:
                self.editing_entry = entry.copy()
                self.edit_entry_id = entry.get("id", 0)
                self.edit_is_applicable = entry.get("is_applicable", True)
                self.edit_implementation_status = entry.get("implementation_status", "")
                self.edit_justification = entry.get("justification", "") or ""
                self.edit_implementation_notes = entry.get("implementation_notes", "") or ""
                self.show_edit_dialog = True
                break

    def close_edit_dialog(self):
        """Close edit dialog."""
        self.show_edit_dialog = False
        self.editing_entry = {}

    def set_edit_is_applicable(self, value: bool):
        """Set is_applicable."""
        self.edit_is_applicable = value

    def set_edit_implementation_status(self, status: str):
        """Set implementation_status."""
        self.edit_implementation_status = status

    def set_edit_justification(self, value: str):
        """Set justification."""
        self.edit_justification = value

    def set_edit_implementation_notes(self, value: str):
        """Set implementation_notes."""
        self.edit_implementation_notes = value

    async def save_entry(self):
        """Save edited entry."""
        if not self.edit_entry_id:
            return

        try:
            await api_client.update_soa_entry(
                self.edit_entry_id,
                {
                    "is_applicable": self.edit_is_applicable,
                    "implementation_status": self.edit_implementation_status,
                    "justification": self.edit_justification,
                    "implementation_notes": self.edit_implementation_notes,
                }
            )
            self.success_message = "Wijzigingen opgeslagen"
            self.show_edit_dialog = False
            self.editing_entry = {}
            await self.load_data()
        except Exception as e:
            self.error = f"Fout bij opslaan: {str(e)}"

    # Initialize wizard
    def open_init_dialog(self):
        """Open initialize SoA wizard with clean state."""
        self.init_scope_id = None
        self.init_standard_id = None
        self.init_requirement_count = 0
        self.init_is_loading = False
        self.init_error = ""
        self.init_success = ""
        self.show_init_dialog = True

    def close_init_dialog(self):
        """Close initialize wizard and reset state."""
        self.show_init_dialog = False
        self.init_scope_id = None
        self.init_standard_id = None
        self.init_requirement_count = 0
        self.init_is_loading = False
        self.init_error = ""
        self.init_success = ""

    def set_init_scope(self, scope_id: str):
        """Set wizard scope selection."""
        if scope_id and scope_id != "NONE":
            self.init_scope_id = int(scope_id)
        else:
            self.init_scope_id = None

    async def set_init_standard(self, standard_id: str):
        """Set wizard standard selection and fetch requirement count."""
        if standard_id and standard_id != "NONE":
            self.init_standard_id = int(standard_id)
            await self._fetch_requirement_count(int(standard_id))
        else:
            self.init_standard_id = None
            self.init_requirement_count = 0

    async def _fetch_requirement_count(self, standard_id: int):
        """Fetch requirement count for preview."""
        try:
            requirements = await api_client.get_requirements_for_standard(standard_id)
            self.init_requirement_count = len(requirements)
        except Exception as e:
            self.init_requirement_count = 0
            print(f"Error fetching requirement count: {e}")

    async def initialize_soa_from_wizard(self):
        """Initialize SoA from wizard state."""
        if not self.init_scope_id or not self.init_standard_id:
            self.init_error = "Selecteer een scope en standaard"
            return

        self.init_is_loading = True
        self.init_error = ""
        self.init_success = ""

        auth = await self.get_state(AuthState)
        tid = auth.tenant_id

        try:
            result = await api_client.initialize_soa_from_standard(
                scope_id=self.init_scope_id,
                standard_id=self.init_standard_id,
                tenant_id=tid,
            )
            created = result.get("created", 0)
            self.init_success = f"SoA geinitialiseerd: {created} entries aangemaakt"
            # Set page filter to show the new entries
            self.selected_scope_id = self.init_scope_id
            await self.load_data()
        except Exception as e:
            self.init_error = f"Fout bij initialiseren: {str(e)}"
        finally:
            self.init_is_loading = False

    def clear_messages(self):
        """Clear success/error messages."""
        self.success_message = ""
        self.error = ""

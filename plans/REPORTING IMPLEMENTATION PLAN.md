Rapportage Feature Implementation Plan
Een "Rapportage" menuknop en pagina toevoegen aan het IMS systeem. Gebruikers kunnen op twee manieren rapporten genereren:

Prompt-based: Via AI-gestuurde tekstprompt
Dropdown-based: Via selectie van Scope, Assets, en Domein (Security/Privacy/BCM)
User Review Required
IMPORTANT

Open vragen die de implementatie beïnvloeden:

Rapport Output: Moet het rapport direct op het scherm getoond worden, of als downloadbare PDF/Word? Of beide?
AI Model: Welke AI moet gebruikt worden voor prompt-based generatie? De bestaande "report" agent uit het chat systeem?
Persistentie: Moeten gegenereerde rapporten opgeslagen worden in de database (via 
ReportExecution
 model), of zijn het transiente/ad-hoc rapporten?
Taal: UI en rapporten in het Nederlands?
Proposed Changes
Frontend Navigation
[MODIFY] 
layout.py
Voeg "Rapportage" link toe aan sidebar navigatie, tussen "Backlog" en de divider (rond regel 53):

diff
nav_link("Backlog", "/backlog", "list-todo"),
+nav_link("Rapportage", "/reports", "file-chart-column"),
 rx.divider(),
Frontend State
[NEW] 
report.py
Nieuw state bestand voor rapport-generatie met:

ReportState class met:
Form fields voor dropdown selecties (selected_scope_id, selected_domain, selected_asset_ids)
Prompt input field (prompt_text)
Generation mode (mode: "prompt" | "dropdown")
Generated report content (report_content, report_html)
Loading states en error handling
Methods:
load_scopes() - Laad beschikbare scopes voor dropdown
load_assets() - Laad assets gebaseerd op geselecteerde scope
generate_report_from_prompt() - AI-gestuurde generatie
generate_report_from_selection() - Dropdown-based generatie
download_report() - Export naar PDF/Word (optioneel)
Frontend Page
[NEW] 
reports.py
Nieuwe pagina met layout bestaande uit:

Header: "Rapportage" titel
Mode Toggle: Tabs of radio buttons om te kiezen tussen "AI Prompt" en "Selectie"
AI Prompt Mode:
Grote text area voor prompt invoer
Voorbeeld prompts als hints/suggestions
"Genereer" knop
Selection Mode:
Dropdown: Scope selectie (verplicht)
Multi-select: Assets (optioneel)
Radio/Select: Domein (Security/Privacy/BCM/Alle)
"Genereer" knop
Report Display Area:
Rendered HTML/Markdown van gegenereerd rapport
Download knoppen (PDF, Word, etc.)
Frontend API Client
[MODIFY] 
client.py
Voeg nieuwe API methods toe:

python
async def generate_report_from_prompt(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate a report using AI from a text prompt."""
    ...
async def generate_report_from_selection(
    self, 
    scope_id: int, 
    domain: str,
    asset_ids: List[int] = None,
) -> Dict[str, Any]:
    """Generate a report based on scope/asset/domain selection."""
    ...
Backend API
[MODIFY] Backend routers (nieuwe endpoint)
Voeg nieuwe endpoint toe voor rapport-generatie. Dit kan via bestaande AI agent infrastructure of een dedicated endpoint:

python
@router.post("/reports/generate")
async def generate_report(
    request: ReportGenerationRequest,
    session: AsyncSession = Depends(get_session),
):
    """Generate a report based on prompt or selection criteria."""
    ...
Verification Plan
Manual Browser Testing
Start de applicatie:

bash
cd x:/ClaudeCode/IMS/frontend
reflex run
Verificeer navigatie:

Log in op de applicatie
Controleer dat "Rapportage" link zichtbaar is in de sidebar
Klik op de link en verifieer dat de pagina laadt
Test Prompt Mode:

Selecteer "AI Prompt" modus
Voer een test prompt in: "Genereer een overzicht van alle open risico's"
Klik "Genereer"
Verifieer dat er een rapport wordt getoond
Test Selection Mode:

Selecteer "Selectie" modus
Kies een Scope uit de dropdown
Selecteer een Domein (bijv. "Security")
Klik "Genereer"
Verifieer dat er een rapport wordt getoond
NOTE

Handmatige browser testing is vereist omdat we UI-interacties en AI-generatie testen die moeilijk te automatiseren zijn zonder volledige end-to-end test setup.

Automated Tests (Optional)
Tests kunnen later toegevoegd worden aan backend/tests/ met het bestaande pytest framework, maar gezien de AI-afhankelijkheid is handmatige verificatie initieel het meest praktisch.
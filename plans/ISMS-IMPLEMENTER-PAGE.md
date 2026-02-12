# ISMS Implementer — Implementatieplan (v2.1)

Nieuwe pagina onder menukop **INRICHTEN** (was DOEN, maar "Inrichten" past beter bij implementatie) die de gebruiker stapsgewijs door een volledige ISMS-implementatie leidt, gebaseerd op ISO 27001 hoofdstuk 4 t/m 10. 
In tegenstelling tot een statische checklist, **creëert dit process daadwerkelijke data** in de database (Context, Stakeholders, Beleid, Risico's, etc.).

---

## 1. Functioneel Ontwerp

### 1.1 Doel
De gebruiker ziet **in één oogopslag** de status van de implementatie en wordt actief begeleid bij het **vastleggen van verplichte informatie** (Context, Stakeholders, Beleid, Risico's).

### 1.2 Stappen & Data Creatie

Met expliciete mapping naar "Contextanalyse" document:

| # | Stap | ISO 27001 | Actie / Data Creatie | Contextanalyse Document |
|---|------|-----------|----------------------|-------------------------|
| 1 | **Context & Organisatie** | H4 — Context | **Create:** <br>- `OrganizationProfile` (Sector, Grootte) <br>- `OrganizationContext` (SWOT/PESTLE) <br>- `Stakeholder` (Belanghebbenden) <br>- `Scope` (Kritische Processen) <br>- `Standard` (Welke wetgeving?) | - H2 (Organisatie) <br>- H3 (Processen) <br>- H4 (Intern/Extern) <br>- H5 (Stakeholders) <br>- H7 (Wetgeving) <br>- Bijlage 1 |
| 2 | **Leiderschap & Beleid** | H5 — Leiderschap | **Create:** <br>- `Policy` (Beleid) <br>- `RiskAppetite` (Risicobereidheid) <br>- `Objective` (Doelstellingen) | - H1 (Kaderstelling) |
| 3 | **Risicomanagement** | H6 — Planning | **Create:** <br>- `Risk` (met `RiskScope` context) <br>- `Threat` (Dreigingen) <br>- `RiskFramework` | - H6 (Dreigingen) |
| 4 | **Middelen & Bewustzijn** | H7 — Ondersteuning | **Create:** <br>- `AwarenessProgram` <br>- `Competence` | (Indirect ondersteunend) |
| 5 | **Beheersing & SoA** | H8 — Uitvoering | **Create:** <br>- `Control` (Implementatie) <br>- `ApplicabilityStatement` (SoA) | (Uitwerking risico's) |
| 6 | **Evaluatie & Audit** | H9 — Evaluatie | **Create:** <br>- `Assessment` (Interne Audit) <br>- `ManagementReview` | (Directiebeoordeling) |
| 7 | **Verbetering (CAPA)** | H10 — Verbetering | **Create:** <br>- `CorrectiveAction` (NC's) <br>- `Initiative` (Verbeterplannen) | (PDCA sluiting) |

### 1.3 UI-concept

De pagina toont een horizontale stepper. Onder de stepper wordt de **actieve stap** uitgelicht met een formulier of actie-knoppen om de ontbrekende data direct in te voeren.

**Voorbeeld Stap 1 (Context):**
- Toont huidige SWOT (indien aanwezig)
- Knop: "Voer SWOT-analyse uit" -> opent modaal/formulier om `OrganizationContext` records aan te maken.
- Lijst met Stakeholders -> Knop "Stakeholder toevoegen" -> opent modaal voor nieuw `Stakeholder` record.
- **[NIEUW]** "Selecteer Wet- en Regelgeving" -> checkbox lijst met `Standard` objecten (BIO, AVG, ISO).

---

## 2. Technisch Ontwerp

### 2.1 Datamodel Uitbreidingen (`backend/app/models/core_models.py`)

Om te voldoen aan ISO 27001 H4.2 (Belanghebbenden) en H4.1 (Context):

#### 2.1.1 Nieuw Model: `Stakeholder`
```python
class Stakeholder(SQLModel, table=True):
    """
    ISO 27001 Clause 4.2: Understanding the needs and expectations of interested parties.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id", index=True)
    
    name: str # e.g. "Klanten", "Toezichthouder", "Medewerkers"
    type: str # "Internal", "External", "Partner"
    
    # Needs & Expectations
    requirements: str # Wat verwachten ze?
    
    # Relevance
    relevance_level: str = "High" # High/Medium/Low
    
    # Link to required controls/policy (optional)
    requirement_id: Optional[int] = Field(default=None, foreign_key="requirement.id")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 2.1.2 Uitbreiding/Gebruik `OrganizationContext`
We gebruiken het bestaande `OrganizationContext` model, maar definiëren standaard `key`-waarden voor structuur:
- `SWOT_STRENGTH`
- `SWOT_WEAKNESS`
- `SWOT_OPPORTUNITY`
- `SWOT_THREAT`
- `PESTLE_POLITICAL`, `PESTLE_ECONOMIC`, etc.

### 2.2 API Endpoints

Bestaande endpoints worden gebruikt waar mogelijk. Nieuwe CRUD-endpoints nodig voor:
- `GET / POST / PUT / DELETE /api/v1/endpoints/stakeholders`

### 2.3 Frontend (`frontend/ims/pages/isms_implementer.py`)

- **State:** `IsmsImplementerState` laadt data van diverse endpoints.
- **Components:**
    - `step_context_component()`: Toont SWOT + Stakeholders tabel.
    - `step_leadership_component()`: Toont Policy status + Risk Appetite slider.
    - ... en zo verder voor elke stap.

---

## 3. Implementatieplan

### Fase 1: Backend
1.  **Model:** `Stakeholder` toevoegen aan `core_models.py`.
2.  **Migratie:** Database migratie genereren (alembic).
3.  **API:** `Stakeholder` router toevoegen (`backend/app/api/v1/endpoints/stakeholders.py`) en registreren in `api.py`.

### Fase 2: Frontend State & Page
1.  **State:** `IsmsImplementerState` maken in `frontend/ims/state/isms_implementer.py`.
    - Loaders voor alle benodigde data (Context, Stakeholders, Policies, etc.).
    - Computed vars voor stap-progressie (bijv. `context_step_completed` = `has_swot` and `has_stakeholders`).
2.  **Page:** `frontend/ims/pages/isms_implementer.py` opzetten met horizontale stepper.

### Fase 3: Stap-specifieke Componenten
1.  **Stap 1 (Context):** Implementeer Stakeholder tabel (add/edit/delete) + SWOT editor.
2.  **Stap 2 t/m 7:** Implementeer "read-only" views met links naar bestaande pagina's (Policy, Risks) OF embedded editors (indien eenvoudig). *Focus eerst op Stap 1 als Proof of Concept.*

---

## 4. Verificatie

1.  **Backend Test:**
    - `test_stakeholders.py`: Create, Read, Update, Delete stakeholder.
    - Controleer of `OrganizationContext` correct SWOT keys opslaat.
2.  **Frontend Test:**
    - Open `/isms-implementer`.
    - Stap 1 is actief.
    - Voeg een stakeholder toe -> data verschijnt in tabel.
    - Stap 1 progress updated naar "Completed" (indien criteria gehaald).

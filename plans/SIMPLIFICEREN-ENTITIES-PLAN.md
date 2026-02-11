# Plan: Vereenvoudigen Scope-Entiteiten (Route A+)

> **Besluit**: De Scope-tabel blijft het fundament (27 FK-referenties intact), maar we herstructureren de hiërarchie en ontkoppelen Assets/Suppliers naar een M2M-pool.

---

## 1. Probleemstelling

| Probleem | Impact |
|----------|--------|
| `ScopeType.ORGANIZATION` dupliceert `Tenant` | Verwarrend voor gebruikers |
| `ScopeType.VIRTUAL` wordt nergens gebruikt | Dode code |
| `ScopeType.CLUSTER` is alleen nodig voor grote orgs | Onnodige complexiteit voor MKB |
| Asset is een **kind** van Process via `parent_id` (1-op-N) | Één MS365-licentie moet 20x aangemaakt worden |
| 7 ScopeTypes in één vlak model | Te flexibel, geen structuur |

## 2. Doelarchitectuur

```
Tenant (= de Organisatie, al bestaand)
  └── [Cluster]          ← optioneel, achter tenant-setting
       └── Department    ← de eigenaar/afdeling (verplicht tussenniveau)
            └── Process  ← wat de afdeling doet (1-op-N strict)

Asset-pool     ←→ Process (N-op-N via ScopeLink)
Supplier-pool  ←→ Process/Asset (N-op-N via ScopeLink)
```

**Strikte bovenkant** (parent_id, 1-op-N): `[Cluster] → Department → Process`
- RBAC vloeit hiërarchisch door
- Governance-status op elk niveau

**Flexibele onderkant** (ScopeLink, N-op-N): `Process ↔ Asset`, `Process ↔ Supplier`
- Geen dubbele invoer van assets
- Eén asset kan meerdere processen bedienen

---

## 3. Wijzigingen per laag

### 3.1 Backend Model: Enum opschonen

**Bestand**: `backend/app/models/core_models.py` regel 59-66

```python
# VOOR:
class ScopeType(str, Enum):
    ORGANIZATION = "Organization"
    CLUSTER = "Cluster"
    DEPARTMENT = "Department"
    PROCESS = "Process"
    ASSET = "Asset"
    SUPPLIER = "Supplier"
    VIRTUAL = "Virtual"

# NA:
class ScopeType(str, Enum):
    CLUSTER = "Cluster"        # Optioneel — alleen als tenant.enable_clusters=True
    DEPARTMENT = "Department"  # Afdeling — de eigenaar
    PROCESS = "Process"        # Wat de afdeling doet
    ASSET = "Asset"            # Middel — leeft in pool, M2M met Process
    SUPPLIER = "Supplier"      # Leverancier — leeft in pool, M2M met Process/Asset
```

**Geschrapt**: `ORGANIZATION` (= Tenant), `VIRTUAL` (nooit gebruikt)

### 3.2 Backend Model: Nieuwe koppeltabel `ScopeLink`

**Bestand**: `backend/app/models/core_models.py`

```python
class ScopeLinkType(str, Enum):
    """Type relatie tussen pool-scopes en hiërarchische scopes"""
    USES = "uses"              # Process gebruikt Asset
    SUPPLIED_BY = "supplied_by"  # Process/Asset wordt geleverd door Supplier
    SUPPORTS = "supports"      # Asset ondersteunt Process (inverse view)

class ScopeLink(SQLModel, table=True):
    """
    Many-to-Many koppeling tussen hiërarchische scopes (Process) en
    pool-scopes (Asset, Supplier). Vervangt parent_id voor Assets/Suppliers.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id", index=True)

    source_scope_id: int = Field(foreign_key="scope.id", index=True)  # Bijv. Process
    target_scope_id: int = Field(foreign_key="scope.id", index=True)  # Bijv. Asset

    link_type: ScopeLinkType = ScopeLinkType.USES
    description: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Unique constraint: geen dubbele links
    __table_args__ = (
        UniqueConstraint("source_scope_id", "target_scope_id", "link_type"),
    )
```

> **Opmerking**: `ScopeDependency` (bestaand) blijft bestaan voor infrastructure-/service-dependencies tussen scopes. `ScopeLink` is specifiek voor de M2M "gebruikt"/"geleverd door"-relatie.

### 3.3 Backend Model: Scope model aanpassen

**Bestand**: `backend/app/models/core_models.py` — `class Scope`

Wijzigingen:
1. **parent_id gedrag wijzigen**: `parent_id` is alleen geldig voor CLUSTER, DEPARTMENT, PROCESS. Voor ASSET en SUPPLIER wordt `parent_id` altijd `NULL` (afgedwongen in business logic).

2. **Nieuwe relationships toevoegen**:
```python
# Op het Scope model:
linked_targets: List["Scope"] = Relationship(
    link_model=ScopeLink,
    sa_relationship_kwargs={
        "primaryjoin": "Scope.id==ScopeLink.source_scope_id",
        "secondaryjoin": "Scope.id==ScopeLink.target_scope_id"
    }
)
linked_sources: List["Scope"] = Relationship(
    link_model=ScopeLink,
    sa_relationship_kwargs={
        "primaryjoin": "Scope.id==ScopeLink.target_scope_id",
        "secondaryjoin": "Scope.id==ScopeLink.source_scope_id"
    }
)
```

3. **Bestaande velden**: Alle conditionele velden (asset_type, vendor_contact_*, BIA ratings, etc.) blijven **ongewijzigd**. Geen JSONB. Typed fields behouden.

### 3.4 Backend Model: VirtualScopeMember deprecaten

**Bestand**: `backend/app/models/core_models.py` regel 884-904

`VirtualScopeMember` wordt niet meer gebruikt nu `VIRTUAL` ScopeType verdwijnt:
- Markeer als deprecated met docstring
- Verwijder niet direct uit model (DB-tabel blijft bestaan voor backward compat)
- Verwijder wel uit imports en API-routes (als die bestaan)

### 3.5 Backend Model: Tenant settings uitbreiden

**Bestand**: `backend/app/models/core_models.py` — `class Tenant`

```python
# Nieuw veld op Tenant:
enable_clusters: bool = False  # MKB=False, Gemeente=True
```

Of opnemen in het bestaande `settings: Optional[str]` JSON-veld als `{"enable_clusters": true}`.

### 3.6 Backend API: Hiërarchie-validatie aanpassen

**Bestand**: `backend/app/api/v1/endpoints/scopes.py` regel 64-72

```python
# VOOR:
hierarchy = [ScopeType.ORGANIZATION, ScopeType.CLUSTER, ScopeType.DEPARTMENT,
             ScopeType.PROCESS, ScopeType.ASSET]

# NA:
hierarchy = [ScopeType.CLUSTER, ScopeType.DEPARTMENT, ScopeType.PROCESS]
# Asset en Supplier zijn NIET in de hiërarchie — ze leven in de pool

# Extra validatie:
if scope.type in [ScopeType.ASSET, ScopeType.SUPPLIER]:
    if scope.parent_id is not None:
        raise HTTPException(400, "Assets en Suppliers mogen geen parent hebben")

if scope.type == ScopeType.CLUSTER:
    tenant = await get_tenant(session, tenant_id)
    if not tenant.enable_clusters:
        raise HTTPException(400, "Clusters zijn niet ingeschakeld voor deze organisatie")
```

### 3.7 Backend API: Bestaande endpoints aanpassen

**Bestand**: `backend/app/api/v1/endpoints/scopes.py`

| Endpoint | Wijziging |
|----------|-----------|
| `GET /` (list scopes) | `scope_type` filter: "Organization" en "Virtual" negeren/weigeren, `is_active=False` standaard uitsluiten |
| `GET /{scope_id}/tree` | Alleen beschikbaar voor hiërarchische types (Cluster/Department/Process). Return 400 voor Asset/Supplier |
| `GET /{scope_id}/children` | Idem — niet relevant voor pool-types |
| `PATCH /{scope_id}/bia` | Ongewijzigd — BIA werkt op Process én Asset |
| `POST /{scope_id}/establish` | Ongewijzigd — governance werkt op alle types |
| `GET /{scope_id}/risks` | Ongewijzigd — RiskScope werkt onafhankelijk |

### 3.8 Backend API: Nieuwe ScopeLink endpoints

**Bestand**: `backend/app/api/v1/endpoints/scopes.py` (uitbreiden)

| Endpoint | Methode | Doel |
|----------|---------|------|
| `POST /{process_id}/assets/{asset_id}` | POST | Koppel asset aan process |
| `DELETE /{process_id}/assets/{asset_id}` | DELETE | Ontkoppel asset van process |
| `GET /{process_id}/assets` | GET | Alle assets van een process |
| `GET /{asset_id}/processes` | GET | Alle processen die een asset gebruiken |
| `POST /{scope_id}/suppliers/{supplier_id}` | POST | Koppel supplier |
| `DELETE /{scope_id}/suppliers/{supplier_id}` | DELETE | Ontkoppel supplier |
| `GET /{scope_id}/suppliers` | GET | Alle suppliers van een scope |

### 3.9 Backend API: CRUD service voor ScopeLink

**Nieuw bestand**: `backend/app/crud/crud_scope_link.py`

Standaard CRUD-operaties:
- `create_link(session, source_id, target_id, link_type, tenant_id)` — met validatie dat source=Process en target=Asset/Supplier
- `delete_link(session, source_id, target_id, link_type, tenant_id)`
- `get_links_for_scope(session, scope_id, direction, tenant_id)` — richting: "outgoing" of "incoming"
- `get_linked_count(session, scope_id, direction)` — voor "Gebruikt door X processen" badge

### 3.10 Backend API: Response model aanpassen

**Bestand**: `backend/app/api/v1/endpoints/scopes.py`

Scope-response uitbreiden met optionele link-informatie:
```python
# Bij GET /scopes (lijst): voeg computed velden toe
{
    "id": 42,
    "type": "Asset",
    "name": "Microsoft 365",
    "linked_process_count": 12,  # NIEUW: hoeveel processen gebruiken dit asset
    ...
}

# Bij GET /scopes/{id} (detail): voeg linked scopes toe
{
    "id": 42,
    "type": "Asset",
    "name": "Microsoft 365",
    "linked_processes": [        # NIEUW: welke processen
        {"id": 5, "name": "Salarisverwerking"},
        {"id": 8, "name": "Facturatie"}
    ],
    ...
}
```

### 3.11 Backend API: RBAC query aanpassen

**Impact**: `UserScopeRole` query moet nu ook via `ScopeLink` zoeken.

```
"Geef alles waar gebruiker X recht op heeft voor Afdeling ICT":
1. Zoek scope_id = ICT (Department)
2. Zoek alle children via parent_id (= Processen onder ICT)
3. Zoek alle linked Assets/Suppliers via ScopeLink voor die Processen
→ Dat is de volledige scope van de gebruiker
```

---

## 4. Frontend wijzigingen (compleet overzicht)

### 4.1 Scopes-pagina

**Bestand**: `frontend/ims/pages/scopes.py`

| Regel | Nu | Straks |
|-------|----|--------|
| 2 | Docstring "Organization hierarchy management" | "Scope hierarchy management" |
| 52 | `rx.select.item("Organisatie", value="Organization")` | **Verwijderen** |
| 448 | `type_badge` — "Organisatie" badge met building-2 icon | **Verwijderen** |
| 648 | Create-dialog: `rx.select.item("Organisatie", value="Organization")` | **Verwijderen** |
| 690 | Stats-card "Organisaties" | **Verwijderen** — vervangen door "Afdelingen" |
| 841 | Subtitle "Organisatie, processen en assets beheren" | "Afdelingen, processen en assets beheren" |
| n.v.t. | Geen "Virtueel" filter/badge | Bevestig dat dit al niet bestaat (was het er nooit) |
| n.v.t. | "Cluster" in type-filter | Conditioneel tonen op basis van `tenant.enable_clusters` |

Nieuw:
- Parent-selectie veld: alleen tonen als type in [Cluster, Department, Process]
- Voor Asset/Supplier: toon "Koppel aan processen" multi-select in plaats van parent

### 4.2 Assets-pagina

**Bestand**: `frontend/ims/pages/assets.py`

| Wijziging | Detail |
|-----------|--------|
| Nieuwe kolom | "Gekoppeld aan" — badge met aantal processen |
| Nieuwe actie | "Koppel aan proces" knop → dialog met process-selectie |
| Detail-weergave | Sectie "Gebruikt door" met lijst van gekoppelde processen |
| Parent-veld | Verwijderen uit create/edit formulier (assets hebben geen parent meer) |

### 4.3 Suppliers-pagina

**Bestand**: `frontend/ims/pages/suppliers.py`

| Wijziging | Detail |
|-----------|--------|
| Nieuwe kolom | "Levert aan" — badge met aantal processen/assets |
| Nieuwe actie | "Koppel aan proces/asset" knop → dialog |
| Detail-weergave | Sectie "Levert aan" met gekoppelde processen en assets |
| Parent-veld | Verwijderen uit create/edit formulier |

### 4.4 Scope State

**Bestand**: `frontend/ims/state/scope.py`

| Regel | Nu | Straks |
|-------|----|--------|
| 64-65 | `organization_count` computed property met type=="Organization" | **Verwijderen** |
| 84+ | `available_parents` — bevat Organization/Cluster types | Filteren: alleen Cluster/Department/Process (afhankelijk van context) |
| n.v.t. | Geen link-functies | **Nieuw**: `link_asset_to_process()`, `unlink_asset()`, `get_linked_assets()`, `get_linked_processes()` |
| n.v.t. | `show_parent_field` | **Nieuw**: alleen True als type in [Cluster, Department, Process] |

### 4.5 Asset State

**Bestand**: `frontend/ims/state/asset.py`

| Regel | Nu | Straks |
|-------|----|--------|
| 90 | Parent-filter bevat `"Organization", "Cluster", "Department", "Process"` | **Verwijderen** — assets hebben geen parent meer |
| n.v.t. | Geen link-state | **Nieuw**: `linked_processes: List[Dict]`, `link_to_process()`, `unlink_from_process()` |

### 4.6 Supplier State

**Bestand**: `frontend/ims/state/supplier.py`

| Regel | Nu | Straks |
|-------|----|--------|
| 89 | Parent-filter bevat `"Organization", "Cluster", "Department", "Process"` | **Verwijderen** — suppliers hebben geen parent meer |
| n.v.t. | Geen link-state | **Nieuw**: `linked_scopes: List[Dict]`, `link_to_scope()`, `unlink_from_scope()` |

### 4.7 Risks-pagina (scope selector)

**Bestand**: `frontend/ims/pages/risks.py` regel 404-473

| Wijziging | Detail |
|-----------|--------|
| Scope-selectie dropdown | Moet alle scope-types tonen (inclusief pool-types Asset/Supplier) |
| Geen structuurwijziging nodig | De scope-selector werkt al type-agnostisch via `scope_id` |

### 4.8 Overige pagina's met scope-referenties

| Bestand | Regel | Wijziging |
|---------|-------|-----------|
| `pages/assessments.py` | Scope-selectie | Geen wijziging nodig — selecteert op `scope_id` |
| `pages/controls.py` | Scope-referenties | Geen wijziging nodig — werkt op `scope_id` |
| `pages/in_control.py` | 24: toont `scope_type` | Geen wijziging nodig — toont type als tekst |
| `pages/users.py` | 607: toont `scope_type` in user-role tabel | Geen wijziging nodig — toont type als tekst |
| `pages/risk_appetite.py` | 46: "Organisatie-breed" label | Houden — dit gaat over tenant-breed, niet ScopeType.Organization |

### 4.9 API Client

**Bestand**: `frontend/ims/api/client.py`

Nieuwe methoden:
```python
async def link_asset_to_process(self, process_id: int, asset_id: int) -> Dict
async def unlink_asset_from_process(self, process_id: int, asset_id: int) -> None
async def get_linked_assets(self, process_id: int) -> List[Dict]
async def get_linked_processes(self, asset_id: int) -> List[Dict]
async def link_supplier(self, scope_id: int, supplier_id: int) -> Dict
async def unlink_supplier(self, scope_id: int, supplier_id: int) -> None
async def get_linked_suppliers(self, scope_id: int) -> List[Dict]
```

### 4.10 Navigation / Layout

**Bestand**: `frontend/ims/components/layout.py`

| Regel | Nu | Straks |
|-------|----|--------|
| 116 | "Mijn Organisatie" link → `/organization` | **Ongewijzigd** — dit is het Tenant-profiel, niet ScopeType |
| 138 | "Organisaties" link → `/tenants` (superuser) | **Ongewijzigd** — dit is tenant-beheer |

Geen navigatie-wijzigingen nodig.

---

## 5. Data-migratie

### 5.1 Alembic migratie stappen

**Stap 1**: Nieuwe tabel aanmaken
```sql
CREATE TABLE scopelink (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenant(id),
    source_scope_id INTEGER NOT NULL REFERENCES scope(id),
    target_scope_id INTEGER NOT NULL REFERENCES scope(id),
    link_type VARCHAR NOT NULL DEFAULT 'uses',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_scope_id, target_scope_id, link_type)
);
CREATE INDEX ix_scopelink_source ON scopelink(source_scope_id);
CREATE INDEX ix_scopelink_target ON scopelink(target_scope_id);
CREATE INDEX ix_scopelink_tenant ON scopelink(tenant_id);
```

**Stap 2**: Bestaande Asset parent_id relaties migreren naar ScopeLink
```sql
-- Alle Assets die nu een Process als parent hebben → maak ScopeLink records
INSERT INTO scopelink (tenant_id, source_scope_id, target_scope_id, link_type)
SELECT s.tenant_id, s.parent_id, s.id, 'uses'
FROM scope s
WHERE s.type = 'Asset' AND s.parent_id IS NOT NULL;

-- Zet parent_id op NULL voor alle Assets
UPDATE scope SET parent_id = NULL WHERE type = 'Asset';
```

**Stap 3**: Idem voor Suppliers
```sql
INSERT INTO scopelink (tenant_id, source_scope_id, target_scope_id, link_type)
SELECT s.tenant_id, s.parent_id, s.id, 'supplied_by'
FROM scope s
WHERE s.type = 'Supplier' AND s.parent_id IS NOT NULL;

UPDATE scope SET parent_id = NULL WHERE type = 'Supplier';
```

**Stap 4**: Organization scopes migreren
```sql
-- Organization scopes: hun children moeten direct aan Tenant hangen
-- Stap 4a: Children van Organization-scopes hangen nu nergens → parent_id naar NULL
UPDATE scope SET parent_id = NULL
WHERE parent_id IN (SELECT id FROM scope WHERE type = 'Organization');

-- Stap 4b: Verplaats scope_id referenties van Organization-scopes naar geen
-- (Risico's/Assessments die aan een Organization-scope hingen → bewaar maar markeer)
-- DIT IS EEN MANUELE CHECK — welke records refereren naar Organization-scopes?

-- Stap 4c: Soft-delete Organization scopes
UPDATE scope SET is_active = FALSE WHERE type = 'Organization';
```

**Stap 5**: Virtual scopes opruimen
```sql
-- Soft-delete VirtualScopeMember records
-- (tabel blijft bestaan voor backward compat, maar geen nieuwe records)
UPDATE scope SET is_active = FALSE WHERE type = 'Virtual';
```

**Stap 6**: Tenant veld toevoegen
```sql
ALTER TABLE tenant ADD COLUMN enable_clusters BOOLEAN DEFAULT FALSE;
```

### 5.2 Rollback strategie

Alle migratie-stappen zijn **reversibel**:
- ScopeLink records bevatten de originele parent-child relatie
- Organization scopes worden soft-deleted (is_active=False), niet hard-deleted
- Enum-waarden worden niet uit de DB verwijderd, alleen uit de Python code
- VirtualScopeMember tabel blijft bestaan

### 5.3 Manuele data-check vóór migratie

Voordat stap 4 draait, controleer:
```sql
-- Hoeveel modellen refereren naar Organization-type scopes?
SELECT 'risk' as model, COUNT(*) FROM risk WHERE scope_id IN (SELECT id FROM scope WHERE type='Organization')
UNION ALL
SELECT 'assessment', COUNT(*) FROM assessment WHERE scope_id IN (SELECT id FROM scope WHERE type='Organization')
UNION ALL
SELECT 'incident', COUNT(*) FROM incident WHERE scope_id IN (SELECT id FROM scope WHERE type='Organization')
-- etc. voor alle 27 modellen met scope_id
```
Als er records zijn: beslis of ze naar een Department/Cluster verplaatst worden of direct naar tenant-niveau.

---

## 6. Agent sync

**Agents die bijgewerkt moeten worden** na deze wijziging:

| Agent | Wijziging |
|-------|-----------|
| `scope_agent.py` | System prompt: nieuwe hiërarchie uitleggen, M2M asset-linking, geen Organization type meer. Tools: link/unlink assets/suppliers |
| `risk_agent.py` | Tools: RBAC query via ScopeLink voor asset-risico's |
| `measure_agent.py` | Scope-contextduidelijkheid: maatregel op asset vs. op proces |
| `supplier_agent.py` | M2M relatie uitleggen, koppel-tooling |
| `admin_agent.py` | Tenant-instelling enable_clusters uitleggen |
| `assessment_agent.py` | Scope-selectie: assessments op pool-assets |

---

## 7. Volgorde van uitvoering

| Fase | Wat | Bestanden | Risico |
|------|-----|-----------|--------|
| **Fase 1** | Enum opschonen + ScopeLink model + ScopeLinkType enum | `core_models.py` | Laag (additief) |
| **Fase 2** | Tenant.enable_clusters veld | `core_models.py` | Laag |
| **Fase 3** | Alembic migratie: ScopeLink tabel + tenant kolom | `alembic/versions/` | Laag (additief) |
| **Fase 4** | CRUD service voor ScopeLink | `crud/crud_scope_link.py` (nieuw) | Laag |
| **Fase 5** | Hiërarchie-validatie aanpassen + bestaande endpoints updaten | `api/v1/endpoints/scopes.py` | Medium |
| **Fase 6** | Nieuwe ScopeLink API-endpoints | `api/v1/endpoints/scopes.py` | Laag (additief) |
| **Fase 7** | Response models uitbreiden (linked_count, linked_processes) | `api/v1/endpoints/scopes.py` | Medium |
| **Fase 8** | RBAC query uitbreiden met ScopeLink | Auth/permissions code | Medium |
| **Fase 9** | Frontend: scope state + API client nieuwe methoden | `state/scope.py`, `state/asset.py`, `state/supplier.py`, `api/client.py` | Medium |
| **Fase 10** | Frontend: scopes-pagina opschonen (Organization/Virtual weg) | `pages/scopes.py` | Medium |
| **Fase 11** | Frontend: assets-pagina (pool-weergave, link-functies) | `pages/assets.py` | Medium |
| **Fase 12** | Frontend: suppliers-pagina (pool-weergave, link-functies) | `pages/suppliers.py` | Medium |
| **Fase 13** | Frontend: enable_clusters UI toggle | `pages/scopes.py` + tenant settings | Laag |
| **Fase 14** | Agent sync (6 agents) | `agents/domains/*.py` | Laag |
| **Fase 15** | Data-migratie bestaande data (na manuele check) | `alembic/versions/` | **Hoog** |

> **Fase 15 (data-migratie) pas uitvoeren als Fase 1-14 getest en stabiel zijn.** Tot die tijd werken oude en nieuwe structuur naast elkaar.

---

## 8. Wat NIET verandert

- **27 modellen met `scope_id` FK**: Geen wijziging. Risk, Assessment, Incident, Policy, etc. blijven gewoon naar `scope.id` wijzen.
- **ScopeDependency tabel**: Blijft bestaan voor infrastructure/service dependencies.
- **Conditionele velden op Scope**: `asset_type`, `vendor_contact_*`, BIA ratings, `rto_hours`, etc. blijven getypeerde velden. Geen JSONB.
- **Governance-velden**: `governance_status`, `scope_motivation`, `in_scope`, `validity_year` — blijven.
- **External integration velden**: `external_id`, `external_source`, `last_synced` — blijven.
- **VirtualScopeMember tabel**: Blijft in DB bestaan (niet droppen), maar wordt niet meer gebruikt.
- **Navigation/layout**: "Mijn Organisatie" en "Organisaties" links in sidebar — dit zijn Tenant-pagina's, geen Scope-pagina's.
- **Risk-appetite pagina**: "Organisatie-breed" label — refereert aan tenant-niveau, niet ScopeType.

---

## 9. Compleet bestandenoverzicht

### Backend — gewijzigd
| Bestand | Sectie | Wat |
|---------|--------|-----|
| `backend/app/models/core_models.py` | 3.1, 3.2, 3.3, 3.4, 3.5 | Enum, ScopeLink model, Scope relationships, VirtualScopeMember deprecation, Tenant veld |
| `backend/app/api/v1/endpoints/scopes.py` | 3.6, 3.7, 3.8, 3.10 | Validatie, bestaande endpoints, nieuwe link-endpoints, response models |
| `backend/app/api/v1/api.py` | — | Router registratie (als ScopeLink apart endpoint-bestand wordt) |

### Backend — nieuw
| Bestand | Sectie | Wat |
|---------|--------|-----|
| `backend/app/crud/crud_scope_link.py` | 3.9 | CRUD operaties voor ScopeLink |
| `backend/alembic/versions/xxx_add_scopelink.py` | 5.1 | Migratie: tabel + indexes |
| `backend/alembic/versions/xxx_migrate_data.py` | 5.1 | Migratie: data-verhuizing (apart script) |

### Frontend — gewijzigd
| Bestand | Sectie | Wat |
|---------|--------|-----|
| `frontend/ims/pages/scopes.py` | 4.1 | Organization/Virtual weg, Cluster conditioneel, stats-cards |
| `frontend/ims/pages/assets.py` | 4.2 | Pool-weergave, link-kolom, koppel-dialog, parent weg |
| `frontend/ims/pages/suppliers.py` | 4.3 | Pool-weergave, link-kolom, koppel-dialog, parent weg |
| `frontend/ims/state/scope.py` | 4.4 | organization_count weg, link-functies, parent-logica |
| `frontend/ims/state/asset.py` | 4.5 | Parent-filter weg, link-state nieuw |
| `frontend/ims/state/supplier.py` | 4.6 | Parent-filter weg, link-state nieuw |
| `frontend/ims/api/client.py` | 4.9 | 7 nieuwe API-methoden voor links |

### Frontend — ongewijzigd (bevestigd)
| Bestand | Reden |
|---------|-------|
| `pages/risks.py` | Scope-selector werkt al type-agnostisch via `scope_id` |
| `pages/assessments.py` | Idem |
| `pages/controls.py` | Idem |
| `pages/in_control.py` | Toont scope_type als tekst — werkt met nieuwe types |
| `pages/users.py` | Toont scope_type in rol-tabel — werkt met nieuwe types |
| `pages/risk_appetite.py` | "Organisatie-breed" = tenant-niveau, niet ScopeType |
| `components/layout.py` | "Mijn Organisatie" / "Organisaties" = Tenant, niet Scope |

---

## 10. Succeskriterium

- [ ] MKB-gebruiker kan processen en assets aanmaken zonder ooit "Organization", "Cluster" of "Virtual" te zien
- [ ] Eén asset (bijv. Microsoft 365) kan aan meerdere processen gekoppeld worden zonder duplicatie
- [ ] Gemeente-gebruiker kan Clusters inschakelen en een diepe boom maken
- [ ] RBAC werkt: rechten op een afdeling vloeien door naar processen EN gekoppelde assets
- [ ] Alle bestaande data is correct gemigreerd (geen orphaned records)
- [ ] Alle 27 modellen die `scope_id` gebruiken werken ongewijzigd
- [ ] Assets-pagina toont "Gebruikt door X processen" badge
- [ ] Suppliers-pagina toont "Levert aan X processen/assets" badge
- [ ] Process-detail toont gekoppelde assets en suppliers

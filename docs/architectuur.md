# GRC-platform — Architectuur

> Voor contributors die begrijpen willen hoe het platform is opgebouwd en waarom.

---

## Vierlaagse architectuur

```
Laag 1: MODEL (Data)     — PostgreSQL 16 + SQLAlchemy 2.0
Laag 2: API   (Logica)   — FastAPI + JWT + RBAC + RLS
Laag 3: TOOLS (UI)       — Next.js 15
Laag 4: AI    (Support)  — Ollama / lokaal taalmodel
```

Het principe: **logica zit in de API, niet in de UI**. De frontend is een dunne glasplaat. Dit maakt alternatieve clients (CLI, integraties, andere UI's) mogelijk zonder de businesslogica te dupliceren.

---

## Database (Laag 1)

**Multi-tenant via Row Level Security**

Elke tabel die tenantdata bevat heeft een `tenant_id`-kolom. PostgreSQL RLS-policies zorgen dat queries automatisch gefilterd worden op de actieve tenant — afgedwongen op databaseniveau, niet alleen in applicatiecode.

Dit betekent: zelfs als er een bug in de API zit die de tenant_id niet meestuurt, levert de database geen data terug.

**Structuur**

| Module | Tabellen |
|--------|----------|
| Auth / tenants | `tenants`, `users`, `roles`, `user_roles` |
| GRC-engine | `risks`, `controls`, `risk_controls`, `assessments`, `findings` |
| Evidence | `evidence_items`, `control_evidence` |
| Incidenten | `incidents`, `incident_timeline` |
| Normen | `frameworks`, `framework_controls`, `control_mappings` |
| IMS-inrichting | `ims_steps`, `step_responses`, `setup_progress` |

**Migraties**

Alembic beheert het schema. Er zijn drie basismigraties:
1. `schema` — alle tabellen aanmaken
2. `rls` — Row Level Security policies instellen
3. `seed` — basis-normenkaders en rollen laden

Nieuwe migraties aanmaken: `docker-compose exec api alembic revision --autogenerate -m "beschrijving"`

---

## API (Laag 2)

**FastAPI + async SQLAlchemy**

Alle endpoints zijn asynchroon. De API volgt REST-conventies: `GET /risks`, `POST /risks`, `PATCH /risks/{id}`, etc.

**Authenticatie**

JWT (HS256). De token bevat `user_id`, `tenant_id` en `role`. Elke request die tenantdata raakt, haalt `tenant_id` uit de token en zet die als RLS-context op de databaseverbinding.

```python
# Vereenvoudigd — zie backend/app/core/auth.py
async def set_tenant_context(db: AsyncSession, tenant_id: str):
    await db.execute(text(f"SET app.current_tenant = '{tenant_id}'"))
```

**RBAC**

Rollen worden gecontroleerd via dependency injection. Elke endpoint declareert welke rollen toegang hebben:

```python
@router.post("/risks", dependencies=[Depends(require_role("ciso", "admin"))])
```

**Router-structuur**

```
backend/app/api/v1/endpoints/
├── auth.py         # login, token refresh
├── risks.py        # risicobeheer
├── controls.py     # maatregelen
├── assessments.py  # audits
├── evidence.py     # bewijsbeheer
├── incidents.py    # incidentregistratie
├── frameworks.py   # normenkaders
├── ims_setup.py    # inrichtingswizard stappen
├── users.py        # gebruikersbeheer
└── tenants.py      # organisatiebeheer (admin only)
```

---

## Frontend (Laag 3)

**Next.js 15 + TypeScript + TailwindCSS v4**

De frontend bevat geen businesslogica. Alle validatie en berekeningen zitten in de API. De UI fetcht data, toont die, en stuurt mutaties naar de API.

**Route-structuur**

```
frontend/src/app/
├── (auth)/login/           # Inlogscherm
├── inrichten/              # IMS-wizard (22 stappen)
│   └── stap/[nummer]/
├── beheer/                 # Dagelijks GRC-gebruik
│   ├── risicos/
│   ├── controls/
│   ├── assessments/
│   ├── incidenten/
│   └── bewijs/
└── admin/                  # Platformbeheer (admin-rol)
    ├── gebruikers/
    └── organisaties/
```

**State management**

SWR voor server-state (data fetching + caching). React Context voor auth-state (user, tenant, token). Geen Redux of andere global state library.

---

## AI (Laag 4)

De AI-laag is adviserend en lokaal. Het platform ondersteunt Ollama met een lokaal gehost model (standaard Mistral).

De AI wordt ingeschakeld via `AI_ENABLED=true` in `.env`. Als de AI-service niet bereikbaar is, werkt het platform gewoon door — zonder AI-hints.

Elke inrichtingsstap kan een contextuele hint ophalen die het model genereert op basis van de normatieve context van die stap (BIO 2.0, ISO 27001, etc.).

---

## Tests

105 backend-tests in `backend/tests/`. Opgebouwd met `pytest` + `httpx` async.

Tests draaien altijd tegen een echte PostgreSQL-testdatabase (geen mocks). Dit voorkomt divergentie tussen test- en productiegedrag.

```bash
docker-compose exec api pytest --tb=short          # alle tests
docker-compose exec api pytest tests/test_risks.py  # één module
```

---

## Designkeuzes

**Waarom FastAPI?** Asynchroon, type-safe via Pydantic, automatische OpenAPI-docs. Geschikt voor een team dat ook Python kent voor datawerk en scripting.

**Waarom Next.js en niet een SPA-framework?** Server-side rendering maakt het eenvoudiger om auth-state consistent te houden. De inrichtingswizard heeft veel server-rond-trips; SSR reduceert de waargenomen laadtijd.

**Waarom lokale AI?** Publieke organisaties mogen veelal geen gevoelige data naar externe AI-diensten sturen. Lokale modellen via Ollama zijn een EU-conforme keuze die geen externe afhankelijkheid introduceert.

**Waarom geen ORM-abstractie bovenop SQLAlchemy?** De RLS-implementatie vereist directe controle over databasesessies en transacties. Een extra ORM-laag zou dat bemoeilijken.

# IMS Product Hardening Plan

**Doel:** IMS audit-defensibel, enterprise-veilig en production-klaar maken.
**Totale doorlooptijd:** ~21-28 weken (5 fasen)
**Prioriteit:** Sequentieel — elke fase bouwt voort op de vorige.

---

## Fase 1 — Security & Multi-Tenant Hardening (4-6 weken)

### 1.1 Tenant-isolatie op database-niveau (PostgreSQL RLS)

**Huidige situatie:** Filtering gebeurt in applicatie-queries.
**Gewenst:** Defense in depth — database weigert data zonder tenant context.

**Technische acties:**

1. Identificeer alle tenant-aware tabellen in `core_models.py` (alles met `tenant_id` of `organization_id`)
2. Schrijf Alembic migratie die per tabel RLS-policies aanmaakt:
   ```sql
   ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;
   CREATE POLICY tenant_isolation ON <table>
     USING (tenant_id = current_setting('app.current_tenant')::uuid);
   ```
3. Pas `db.py` session-management aan: elke request doet `SET app.current_tenant = <tenant_id>` voor query-executie
4. Maak een test-suite die verifieert: query zonder tenant context = 0 rows
5. Voeg database-role toe die RLS niet kan bypassen (niet superuser voor app-connectie)

**Bestanden:**
- `backend/app/core/db.py` — session middleware aanpassen
- `backend/app/models/core_models.py` — tenant_id audit op alle modellen
- Nieuwe migratie in `backend/alembic/versions/`
- `backend/tests/test_rls.py` — isolatie-tests

**Deliverables:**
- [ ] RLS actief op 100% tenant-tabellen
- [ ] Test: query zonder tenant context = 0 rows
- [ ] App-connectie draait niet als superuser

---

### 1.2 Break-Glass mechanisme

**Huidige situatie:** `is_superuser` bypass in RBAC.
**Gewenst:** Gecontroleerd noodtoegang-mechanisme met volledige audit trail.

**Nieuw model in `core_models.py`:**

```python
class BreakGlassSession(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    reason: str
    ticket_reference: str  # extern ticketnummer
    approved_by: uuid.UUID = Field(foreign_key="user.id")
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None
```

**Logica:**
- Alleen gebruiker met rol `Admin` (of capability `platform_admin`) kan initiëren
- TTL maximaal 4 uur
- MFA step-up verplicht voor activatie
- Alles gelogd in AuditLog
- Background task voor auto-expire (check elke minuut)

**Technische acties:**
1. Voeg `BreakGlassSession` toe aan `core_models.py`
2. Maak endpoint `POST /api/v1/admin/break-glass` met approval-flow
3. Verwijder alle `is_superuser` checks uit RBAC dependencies
4. Vervang door `has_break_glass_session()` dependency die TTL + revocation checkt
5. Schrijf background task (asyncio / celery) voor auto-expire
6. Log elke actie tijdens break-glass sessie met `break_glass_session_id`

**Bestanden:**
- `backend/app/models/core_models.py` — nieuw model
- `backend/app/api/v1/endpoints/admin.py` — break-glass endpoints
- `backend/app/api/deps.py` — RBAC dependencies aanpassen
- `backend/app/core/tasks.py` — auto-expire task

**Deliverables:**
- [ ] `is_superuser` bypass volledig verwijderd
- [ ] Break-glass enforced in RBAC dependency
- [ ] Auto-expire werkt
- [ ] Volledige audit trail van break-glass sessies

---

### 1.3 Capability-based authorization

**Huidige situatie:** Coarse role-based checks (`require_editor`, `require_configurer`).
**Gewenst:** Fine-grained capability matrix.

**Capabilities (initieel):**

| Capability | Beschrijving |
|---|---|
| `view_core` | Lezen van kerndata |
| `edit_core` | Bewerken van kerndata |
| `configure_scope` | Scopes aanmaken/wijzigen |
| `manage_users` | Gebruikersbeheer |
| `accept_risk` | Risico accepteren/afwijzen |
| `create_finding` | Bevindingen registreren |
| `close_finding` | Bevindingen sluiten |
| `assign_action` | Corrigerende acties toewijzen |
| `close_action` | Corrigerende acties sluiten |
| `platform_admin` | Platformbeheer |

**Technische acties:**
1. Maak `Capability` enum of config-tabel
2. Maak `RoleCapabilityMapping` tabel (role → capabilities)
3. Voeg capabilities toe aan JWT claims (cached)
4. Schrijf `require_capability("accept_risk")` dependency
5. Refactor alle endpoints: vervang role-checks door capability-checks
6. Migratie: seed default role→capability mappings

**Bestanden:**
- `backend/app/models/core_models.py` — Capability model/enum
- `backend/app/api/deps.py` — `require_capability()` dependency
- Alle endpoint-bestanden in `backend/app/api/v1/endpoints/` — refactor checks
- `backend/app/core/auth.py` — JWT capability injection

**Deliverables:**
- [ ] Geen endpoint gebruikt nog `require_editor` of `require_configurer`
- [ ] Alle kritieke operaties hebben specifieke capability
- [ ] Capabilities gecached in JWT

---

## Fase 2 — Audit & Forensics Hardening (3-4 weken)

### 2.1 AuditLog uitbreiden naar forensische reconstructie

**Huidige situatie:** Basis CRUD logging.
**Gewenst:** Volledige forensische reconstructie mogelijk.

**Uitbreiding AuditLog velden:**

| Veld | Type | Doel |
|---|---|---|
| `before_json` | JSONB | State voor wijziging |
| `after_json` | JSONB | State na wijziging |
| `diff_json` | JSONB | Berekend verschil |
| `request_id` | UUID | Correlatie per HTTP request |
| `correlation_id` | UUID | Correlatie over meerdere requests |
| `user_agent` | str | Browser/client identificatie |
| `ip_address` | str | Bron-IP |
| `ai_interaction_id` | UUID (nullable) | Link naar AI-sessie indien van toepassing |

**Constraints:**
- AuditLog tabel is **immutable**: geen UPDATE of DELETE toegestaan (DB-level REVOKE)
- Retention policy: minimaal 7 jaar (configureerbaar)

**Technische acties:**
1. Extend `AuditLog` model met bovenstaande velden
2. Schrijf middleware die `request_id` en `correlation_id` injecteert
3. Implementeer `before/after/diff` capture in CRUD operaties
4. Revoke UPDATE/DELETE op audit-tabel voor app database-rol
5. Schrijf verificatie-tests

**Deliverables:**
- [ ] AuditLog bevat before/after/diff voor elke mutatie
- [ ] Request correlation werkend
- [ ] Immutability enforced op DB-niveau

---

### 2.2 AI Governance Logging

**Nieuw model:**

```python
class AIInvocation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    agent: str                    # welke domain agent
    model: str                    # welk AI model
    prompt_hash: str              # SHA-256 van de prompt
    input_context_ids: list[uuid.UUID]  # welke entities als context
    output_hash: str              # SHA-256 van het antwoord
    confidence: Optional[float]
    accepted: Optional[bool]      # human decision
    accepted_by: Optional[uuid.UUID]
    accepted_at: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Regels:**
- Geen AI-actie wordt persistent zonder human accept/reject
- Elke AI-output wordt gehasht en gelogd
- Dashboard: acceptance rate per agent, confidence distributie

**Technische acties:**
1. Voeg `AIInvocation` toe aan modellen
2. Pas agent-framework aan: elke AI-call logt via `AIInvocation`
3. Voeg accept/reject endpoint toe
4. Block persistence van AI-output zonder acceptance

**Deliverables:**
- [ ] Elke AI-interactie gelogd
- [ ] Human-in-the-loop enforced
- [ ] Acceptance metrics beschikbaar

---

### 2.3 Integrity Controls

**Technische acties:**
1. Database checksum job: dagelijks SHA-256 over kritieke tabellen
2. Daily audit consistency check: vergelijk checksum met vorige run
3. Signed report exports: PDF/CSV exports krijgen hash + timestamp
4. Alerting bij checksum-mismatch

**Deliverables:**
- [ ] Dagelijkse integrity check actief
- [ ] Signed exports werkend
- [ ] Alert bij anomalie

---

## Fase 3 — Continuous Control Monitoring (6-8 weken)

> Dit is functioneel de belangrijkste stap.

### 3.1 Nieuwe entiteiten

```python
class ControlTestDefinition(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    control_id: uuid.UUID = Field(foreign_key="measure.id")
    test_type: str        # "manual" | "automated"
    frequency: str        # cron-expressie of interval
    evidence_required: bool
    success_criteria: str  # beschrijving of JSON-schema
    created_at: datetime
    updated_at: datetime

class ControlTestRun(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    definition_id: uuid.UUID = Field(foreign_key="controltestdefinition.id")
    executed_at: datetime
    executed_by: uuid.UUID = Field(foreign_key="user.id")
    result: str           # "pass" | "fail" | "partial"
    evidence_id: Optional[uuid.UUID] = Field(foreign_key="evidence.id")
    notes: Optional[str]
```

### 3.2 Scheduling engine

**Technische acties:**
1. Kies task-engine: Celery (Redis broker) of `apscheduler` (lighter)
2. Implementeer cron-like scheduling per ControlTestDefinition
3. Overdue detection: als `last_run + frequency < now()` → status "overdue"
4. Dashboard alerts voor overdue controls
5. Notificaties (email / in-app) bij overdue

### 3.3 SoA dependency rule

**Business rule:**
> SoA-status "Implemented" is alleen geldig indien:
> 1. Er een gekoppelde Control (Measure) bestaat
> 2. De laatste test run = PASS
> 3. De test run niet verlopen is (binnen frequency window)

**Technische acties:**
1. Voeg validatie toe aan SoA-status endpoint
2. Maak computed property `is_effectively_implemented` op Requirement/Measure
3. Dashboard toont "Implemented but untested" als warning
4. Block SoA export met ongeldige statussen (of markeer als non-compliant)

### 3.4 Dashboard uitbreiden

**Nieuwe metrics:**
- % controls getest in laatste 90 dagen
- % failed controls
- Control health trend (time series)
- Top failing domains
- SoA compliance score (rekening houdend met test-validiteit)

**Deliverables:**
- [ ] ControlTestDefinition + ControlTestRun modellen live
- [ ] Scheduling engine draait
- [ ] Overdue alerts werkend
- [ ] SoA-validatie enforced
- [ ] Dashboard metrics zichtbaar

---

## Fase 4 — Workflow Enforcement & Governance Guards (4 weken)

### 4.1 Hard gates

| Entiteit | Conditie | Gate |
|---|---|---|
| **Risk** | Residueel risico > appetite threshold | Decision verplicht |
| **Finding** | Status → Closed | CorrectiveAction complete + verificatie aanwezig |
| **Exception** | Verlopen | Auto-escalatie alert |
| **Scope** | Governance expiry | Auto-warning + dashboard flag |

**Technische acties:**
1. Implementeer gate-checks als pre-transition validators
2. Weiger status-update als gate niet voldaan
3. Return duidelijke foutmelding met missende voorwaarden
4. Escalatie-engine voor verlopen exceptions en scopes

### 4.2 Workflow engine hardening

**Technische acties:**
1. Definieer state machines per entiteit (JSON/code config):
   - Risk: `identified → assessed → treated → accepted/mitigated → monitored`
   - Finding: `open → in_progress → resolved → verified → closed`
   - Policy: `draft → review → approved → published → retired`
2. Server-side validatie: alleen geldige transitions toegestaan
3. Transition reason verplicht (minimaal 10 karakters)
4. AuditLog registreert elke transition met from/to/reason/user

**Deliverables:**
- [ ] Alle hard gates geïmplementeerd
- [ ] State machine validatie server-side
- [ ] Geen status-update zonder geldige transition
- [ ] Transition reason verplicht en gelogd

---

## Fase 5 — Enterprise Readiness (4-6 weken)

### 5.1 SSO & Identity

**Technische acties:**
1. Integreer SAML 2.0 en/of OIDC (library: `python-saml` / `authlib`)
2. Azure AD / Entra ID als eerste target
3. SCIM 2.0 user provisioning endpoint voor automated user sync
4. Fallback naar lokale auth voor break-glass scenarios

**Deliverables:**
- [ ] SAML/OIDC login werkend
- [ ] Azure AD getest
- [ ] SCIM provisioning actief

### 5.2 Secrets & Environment Hardening

**Technische acties:**
1. Audit alle plaintext secrets in `.env`, config, code
2. Integreer secret manager (HashiCorp Vault of Azure Key Vault)
3. Rotating signing keys voor JWT (key rotation schedule)
4. Verwijder hardcoded secrets uit codebase (git history scrub indien nodig)

**Deliverables:**
- [ ] Geen plaintext secrets in config
- [ ] Vault-integratie werkend
- [ ] Key rotation geautomatiseerd

### 5.3 Observability

**Technische acties:**
1. Structured logging (JSON format) via `structlog` of `python-json-logger`
2. Central log export naar ELK / Grafana Loki
3. Prometheus metrics endpoint (`/metrics`) met:
   - Failed RBAC checks counter
   - Failed RLS checks counter
   - AI invocation failures counter
   - Workflow violation counter
   - Request latency histogram
4. Grafana dashboards voor ops team

**Deliverables:**
- [ ] Structured JSON logging
- [ ] Central log aggregation
- [ ] Prometheus metrics + Grafana dashboards

### 5.4 Backups & Disaster Recovery

**Technische acties:**
1. Automated daily PostgreSQL backups (pg_dump + WAL archiving)
2. Backup naar off-site storage (S3-compatible of Azure Blob)
3. Restore test pipeline: maandelijkse automated restore test
4. RPO/RTO documentatie:
   - **RPO target:** 1 uur (WAL archiving)
   - **RTO target:** 4 uur (full restore + verification)
5. DR runbook schrijven

**Deliverables:**
- [ ] Dagelijkse backups geautomatiseerd
- [ ] Restore test pipeline actief
- [ ] RPO/RTO gedocumenteerd en getest
- [ ] DR runbook beschikbaar

---

## Implementatievolgorde & Prioriteit

| # | Onderdeel | Fase | Geschatte duur | Afhankelijkheid |
|---|---|---|---|---|
| 1 | Tenant RLS | 1.1 | 2 weken | - |
| 2 | Break-glass | 1.2 | 1.5 weken | - |
| 3 | Capability-based RBAC | 1.3 | 2.5 weken | Break-glass (1.2) |
| 4 | AuditLog uitbreiden | 2.1 | 2 weken | - |
| 5 | AI Governance Logging | 2.2 | 1.5 weken | AuditLog (2.1) |
| 6 | Integrity Controls | 2.3 | 1 week | AuditLog (2.1) |
| 7 | Control Test entiteiten | 3.1 | 1.5 weken | - |
| 8 | Scheduling engine | 3.2 | 2.5 weken | Control Tests (3.1) |
| 9 | SoA dependency rule | 3.3 | 1.5 weken | Control Tests (3.1) |
| 10 | Dashboard metrics | 3.4 | 2 weken | Scheduling (3.2) |
| 11 | Hard gates | 4.1 | 2 weken | Capability RBAC (1.3) |
| 12 | Workflow engine | 4.2 | 2 weken | Hard gates (4.1) |
| 13 | SSO/OIDC | 5.1 | 2.5 weken | Capability RBAC (1.3) |
| 14 | Secrets hardening | 5.2 | 1.5 weken | - |
| 15 | Observability | 5.3 | 2 weken | Structured logging first |
| 16 | Backups & DR | 5.4 | 1.5 weken | - |

---

## Resultaat na implementatie

Na volledige uitvoering is IMS:

- **Multi-tenant veilig op DB-niveau** — RLS voorkomt data-lekkage zelfs bij applicatie-bugs
- **Geen verborgen superuser achterdeur** — break-glass met audit trail en TTL
- **Capability-gedreven autorisatie** — fine-grained, auditeerbaar, uitbreidbaar
- **Forensisch reconstrueerbaar** — before/after/diff op elke mutatie
- **AI governance compliant** — human-in-the-loop enforced, elke AI-actie gelogd
- **Continuous control monitoring** — controls worden actief getest, niet alleen gedocumenteerd
- **Workflow-enforced** — geen shortcuts, elke transition gevalideerd
- **Audit-proof voor ISO 27001 / NEN 7510 / BIO**
- **Verkoopbaar aan enterprise klanten** — SSO, observability, DR

---

## Relatie met bestaande codebase

| Bestaand bestand | Impact |
|---|---|
| `backend/app/models/core_models.py` | Nieuwe modellen: BreakGlassSession, AIInvocation, ControlTestDefinition, ControlTestRun, Capability |
| `backend/app/api/deps.py` | Volledige refactor: capability-based auth |
| `backend/app/core/db.py` | RLS tenant context injection |
| `backend/app/api/v1/endpoints/*` | Alle endpoints: capability checks |
| `backend/app/agents/domains/*` | AI governance logging integratie |
| `backend/app/core/config.py` | Vault-integratie, structured logging config |
| `docker-compose.yml` | Redis (Celery), Prometheus, Grafana, Vault |
| Nieuwe: `backend/app/core/tasks.py` | Background tasks (expire, scheduling, integrity) |
| Nieuwe: `backend/app/core/workflow.py` | State machine engine |
| Nieuwe: `backend/app/core/metrics.py` | Prometheus metrics |

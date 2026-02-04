# IMS Test Plannen

Dit document bevat gedetailleerde testplannen voor elke implementatiefase.

---

## Fase 1: Foundation - Test Plan

### 1.1 Database & Migraties

| Test ID | Test Case | Type | Acceptatiecriteria |
|---------|-----------|------|-------------------|
| F1-DB-01 | Database connectie | Integration | PostgreSQL connectie succesvol |
| F1-DB-02 | pgvector extensie | Integration | `CREATE EXTENSION vector` werkt |
| F1-DB-03 | Alembic migratie up | Integration | `alembic upgrade head` zonder errors |
| F1-DB-04 | Alembic migratie down | Integration | `alembic downgrade -1` zonder errors |
| F1-DB-05 | Schema creatie | Integration | Alle 85+ tabellen aangemaakt |
| F1-DB-06 | Foreign keys | Unit | Relaties correct gedefinieerd |

**Handmatige test stappen:**
```bash
# Start database
docker-compose up -d db

# Test connectie
psql -h localhost -U postgres -d ims -c "SELECT 1"

# Test pgvector
psql -h localhost -U postgres -d ims -c "CREATE EXTENSION IF NOT EXISTS vector"

# Test migraties
cd backend
alembic upgrade head
alembic current
alembic downgrade -1
alembic upgrade head
```

---

### 1.2 FastAPI Basis

| Test ID | Test Case | Type | Acceptatiecriteria |
|---------|-----------|------|-------------------|
| F1-API-01 | Server start | Smoke | `uvicorn` start zonder errors |
| F1-API-02 | Health endpoint | Integration | `GET /health` returns 200 |
| F1-API-03 | OpenAPI docs | Integration | `GET /docs` laadt Swagger UI |
| F1-API-04 | CORS headers | Integration | CORS headers aanwezig in response |
| F1-API-05 | Error handling | Unit | 404/500 responses correct format |

**Handmatige test stappen:**
```bash
# Start API
cd backend
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs
curl http://localhost:8000/api/v1/risks/
```

---

### 1.3 Core CRUD Endpoints

| Test ID | Test Case | Type | Acceptatiecriteria |
|---------|-----------|------|-------------------|
| F1-CRUD-01 | Create Risk | Integration | POST /risks/ returns 200 + created object |
| F1-CRUD-02 | Read Risk | Integration | GET /risks/{id} returns object |
| F1-CRUD-03 | Update Risk | Integration | PATCH /risks/{id} updates fields |
| F1-CRUD-04 | Delete Risk | Integration | DELETE /risks/{id} removes object |
| F1-CRUD-05 | List Risks | Integration | GET /risks/ returns array |
| F1-CRUD-06 | Filter Risks | Integration | Query params filter results |
| F1-CRUD-07 | Pagination | Integration | skip/limit params work |
| F1-CRUD-08 | Create Measure | Integration | POST /measures/ returns 200 |
| F1-CRUD-09 | Create Scope | Integration | POST /scopes/ returns 200 |
| F1-CRUD-10 | Create Tenant | Integration | POST /tenants/ returns 200 |

**Pytest tests:** `backend/tests/test_risks.py`

---

### 1.4 Multi-Tenancy

| Test ID | Test Case | Type | Acceptatiecriteria |
|---------|-----------|------|-------------------|
| F1-MT-01 | Tenant header required | Integration | Request zonder X-Tenant-ID faalt |
| F1-MT-02 | Tenant isolation read | Integration | Tenant 1 ziet geen data van Tenant 2 |
| F1-MT-03 | Tenant isolation write | Integration | Create zet correct tenant_id |
| F1-MT-04 | Cross-tenant access denied | Security | GET op andere tenant's object = 404 |
| F1-MT-05 | Tenant in all queries | Code Review | Alle endpoints gebruiken tenant filter |

**Test stappen:**
```bash
# Create data for tenant 1
curl -X POST http://localhost:8000/api/v1/risks/ \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"title": "Tenant 1 Risk", "tenant_id": 1}'

# Verify tenant 2 cannot see it
curl http://localhost:8000/api/v1/risks/ \
  -H "X-Tenant-ID: 2"
# Should return empty array or not include Tenant 1's risk
```

---

## Fase 2: Core Features - Test Plan

### 2.1 Workflow Engine

| Test ID | Test Case | Type | Acceptatiecriteria |
|---------|-----------|------|-------------------|
| F2-WF-01 | Policy: Draft → Review | Integration | State transition succeeds |
| F2-WF-02 | Policy: Review → Approved | Integration | State transition succeeds |
| F2-WF-03 | Policy: Approved → Published | Integration | State transition succeeds |
| F2-WF-04 | Policy: Published → Archived | Integration | State transition succeeds |
| F2-WF-05 | Policy: Skip step blocked | Integration | Draft → Published fails |
| F2-WF-06 | Policy: Reject returns to Draft | Integration | Review → Draft succeeds |
| F2-WF-07 | Policy: Edit blocked when Published | Integration | PATCH on Published fails |
| F2-WF-08 | Policy: Delete blocked when Published | Integration | DELETE on Published fails |
| F2-WF-09 | Policy: New version creates Draft | Integration | POST /new-version creates v2 |
| F2-WF-10 | Risk acceptance workflow | Integration | Accept sets risk_accepted=true |

**Pytest tests:** `backend/tests/test_policies.py`

---

### 2.2 Assessment Module

| Test ID | Test Case | Type | Acceptatiecriteria |
|---------|-----------|------|-------------------|
| F2-AS-01 | Create Assessment | Integration | POST /assessments/ returns 200 |
| F2-AS-02 | Assessment types | Integration | Audit/DPIA/Pentest types supported |
| F2-AS-03 | Add Finding | Integration | POST /assessments/{id}/findings works |
| F2-AS-04 | Add Evidence | Integration | POST /findings/{id}/evidence works |
| F2-AS-05 | Assessment lifecycle | Integration | Planned → Active → Completed |
| F2-AS-06 | Link to Scope | Integration | Assessment linked to scope |
| F2-AS-07 | Questions & Responses | Integration | Self-assessment flow works |

**Test stappen:**
```bash
# Create assessment
curl -X POST http://localhost:8000/api/v1/assessments/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Q1 Audit", "assessment_type": "Internal Audit", "tenant_id": 1}'

# Add finding
curl -X POST http://localhost:8000/api/v1/assessments/1/findings \
  -H "Content-Type: application/json" \
  -d '{"title": "Missing policy", "severity": "Medium"}'
```

---

### 2.3 Compliance/SoA Module

| Test ID | Test Case | Type | Acceptatiecriteria |
|---------|-----------|------|-------------------|
| F2-SOA-01 | Initialize SoA from Standard | Integration | Creates entries for all requirements |
| F2-SOA-02 | Update applicability | Integration | PATCH is_applicable works |
| F2-SOA-03 | Link measure to requirement | Integration | MeasureRequirementLink created |
| F2-SOA-04 | Gap analysis | Integration | Returns non-compliant requirements |
| F2-SOA-05 | SoA summary | Integration | Returns compliance percentages |
| F2-SOA-06 | Multiple standards | Integration | BIO + ISO 27001 both supported |

**Test stappen:**
```bash
# Create standard with requirements
curl -X POST http://localhost:8000/api/v1/standards/ \
  -d '{"name": "BIO", "version": "1.0"}'

# Initialize SoA
curl -X POST http://localhost:8000/api/v1/soa/scope/1/initialize-from-standard/1

# Get gaps
curl http://localhost:8000/api/v1/soa/scope/1/gaps
```

---

### 2.4 Reporting

| Test ID | Test Case | Type | Acceptatiecriteria |
|---------|-----------|------|-------------------|
| F2-RP-01 | Executive dashboard | Integration | Returns summary stats |
| F2-RP-02 | Risk heatmap data | Integration | Returns quadrant counts |
| F2-RP-03 | Compliance overview | Integration | Returns compliance % |
| F2-RP-04 | Filter by tenant | Integration | Reports respect tenant |
| F2-RP-05 | Filter by scope | Integration | Reports filter by scope |

---

### 2.5 Incident Management

| Test ID | Test Case | Type | Acceptatiecriteria |
|---------|-----------|------|-------------------|
| F2-IN-01 | Create Incident | Integration | POST /incidents/ returns 200 |
| F2-IN-02 | Severity levels | Integration | Critical/High/Medium/Low supported |
| F2-IN-03 | Data breach flag | Integration | is_data_breach field works |
| F2-IN-04 | Link to Risk | Integration | Incident links to existing risk |
| F2-IN-05 | Corrective Action | Integration | Create CA from incident |
| F2-IN-06 | Incident timeline | Integration | Status changes logged |

---

### 2.6 Measures/Controls

| Test ID | Test Case | Type | Acceptatiecriteria |
|---------|-----------|------|-------------------|
| F2-ME-01 | Create Measure | Integration | POST /measures/ returns 200 |
| F2-ME-02 | Activate Measure | Integration | POST /measures/{id}/activate works |
| F2-ME-03 | Deactivate Measure | Integration | POST /measures/{id}/deactivate works |
| F2-ME-04 | Effectiveness score | Integration | PATCH effectiveness works |
| F2-ME-05 | Link to Risk | Integration | POST /measures/{id}/risks/{rid} works |
| F2-ME-06 | Link to Requirement | Integration | POST /measures/{id}/requirements/{rid} works |
| F2-ME-07 | Stats by status | Integration | GET /measures/stats/by-status works |
| F2-ME-08 | RAG indexing | Integration | Measure indexed on create |

**Pytest tests:** `backend/tests/test_measures.py`

---

## Test Execution Checklist

### Pre-Test Setup
- [ ] Docker containers running (`docker-compose up -d`)
- [ ] Database migrated (`alembic upgrade head`)
- [ ] API running (`uvicorn app.main:app --reload`)
- [ ] Test data seeded (if applicable)

### Fase 1: Foundation
- [ ] F1-DB-01 through F1-DB-06
- [ ] F1-API-01 through F1-API-05
- [ ] F1-CRUD-01 through F1-CRUD-10
- [ ] F1-MT-01 through F1-MT-05

### Fase 2: Core Features
- [ ] F2-WF-01 through F2-WF-10
- [ ] F2-AS-01 through F2-AS-07
- [ ] F2-SOA-01 through F2-SOA-06
- [ ] F2-RP-01 through F2-RP-05
- [ ] F2-IN-01 through F2-IN-06
- [ ] F2-ME-01 through F2-ME-08

### Post-Test
- [ ] All critical tests passed
- [ ] Defects logged in backlog
- [ ] Test report generated

---

## Defect Template

```markdown
## Defect: [ID] [Title]

**Test Case:** F1-XX-XX
**Severity:** Critical / High / Medium / Low
**Status:** Open / In Progress / Resolved

**Steps to Reproduce:**
1. ...
2. ...

**Expected Result:**
...

**Actual Result:**
...

**Environment:**
- OS:
- Python:
- Database:

**Notes:**
...
```

---

*Gegenereerd op 4 februari 2025*

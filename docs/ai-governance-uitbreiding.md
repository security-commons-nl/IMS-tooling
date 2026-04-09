# AI Governance Uitbreiding — Roadmap Input

> Inzichten uit externe bronnen (april 2026) die relevant zijn voor de uitbreiding van het GRC-platform met AI-governance functionaliteit.

---

## 1. NIST AI Risk Management Framework (AI RMF)

**Bron:** Ricardo Valdes (LinkedIn, maart 2026)

Het NIST AI RMF is een internationaal referentiekader voor AI-risicobeheer. Het platform ondersteunt momenteel BIO 2.0, ISO 27001, ISO 27701, ISO 22301 en AVG via de Rosetta Stone-mapping. NIST AI RMF is een logische uitbreiding.

### De vier kernfuncties

| Functie | Kernvraag | Platform-mapping |
|---------|-----------|-----------------|
| **GOVERN** | Hoe is AI-risicobeheer georganiseerd? | Inrichtingsmodule stap 3 (Beleid) + governance-configuratie |
| **MAP** | Welke AI-risico's zijn er? | Risico-register uitbreiden met AI-categorie |
| **MEASURE** | Hoe ernstig zijn de risico's? | Assessment-module + AI-specifieke risicoscore |
| **MANAGE** | Hoe worden risico's behandeld? | Controls, bevindingen, correctieve acties |

### Implementatie-voorstel

1. **Voeg NIST AI RMF toe als normenkader** in `ims_standards` — naast BIO, ISO 27001
2. **Maak AI-risico een subcategorie** in het risico-register (`ims_risks.category = 'ai'`)
3. **Rosetta Stone uitbreiding**: map NIST AI RMF requirements naar bestaande BIO/ISO controls
4. **Nieuw assessment-type**: "AI Conformiteitsbeoordeling" (EU AI Act vereiste voor hoog-risico systemen)

---

## 2. AI Governance Architecture Component

**Bron:** Kamilla Harcej (LinkedIn, maart 2026)

### Vier bouwstenen die het platform kan ondersteunen

**AI Inventory & Register**
- Een AI-systemenregister als uitbreiding op het bestaande normen-register
- Per AI-systeem: type, leverancier, risicoclassificatie (EU AI Act-categorie), verantwoordelijke
- Koppeling aan EU AI Act-conformiteitsbeoordeling
- _Implementatie:_ Nieuwe tabel `ims_ai_systems` of gebruik bestaande `ims_scopes` met AI-type

**Risk Assessment Framework**
- AI-specifieke risicobeoordeling: bias, explainability, datakwaliteit, adversarial AI
- Integratie met bestaande IRAM/DPIA-workflows (AVG-overlap)
- _Implementatie:_ AI-subcategorie in `ims_risks`, aanvullende risicofactoren

**Human Oversight Mechanisms**
- Definieer wanneer menselijk ingrijpen verplicht is bij AI-beslissingen
- Escalatiepaden, audit trails voor AI-gestuurde aanbevelingen
- _Implementatie:_ AI-audit log uitbreiden (al aanwezig: `ai_audit_logs`) + HITL-checkpoints

**Monitoring & Continuous Assessment**
- Continue monitoring van AI-systemen op drift, afwijkend gedrag
- Periodieke her-evaluatie van risicoclassificatie
- _Implementatie:_ Cron-based assessment planning (al aanwezig in assessment-module)

---

## 3. Non-Human Identities (NHI) als IAM-component

**Bron:** Cloud Security Alliance (CSA), Sunnykumar K. (LinkedIn, maart 2026)

Het platform gebruikt momenteel RBAC met 6 menselijke rollen. AI-agents en service accounts zijn een nieuwe identiteitscategorie die IAM-uitbreiding vereist.

### Aanbevolen uitbreidingen

**Korte termijn (Fase 2):**
- Service account tokens voor API-integraties (afzonderlijk van user JWT's)
- Agent-token type toevoegen aan auth-laag (naast dev-token en user-token)
- NHI-activiteit apart loggen in `ai_audit_logs`

**Langere termijn (Fase 3):**
- Machine identity management: elke AI-agent krijgt een unieke identiteit
- JIT-toegang voor agents die tijdelijk verhoogde rechten nodig hebben
- NHI-inventaris: welke agents zijn actief, wat zijn hun rechten, wie is eigenaar?

### Implementatie-voorstel (service account token)

```python
# backend/app/core/auth.py — uitbreiding voor agent-tokens
def create_agent_token(agent_id: str, tenant_id: str, scope: list[str], ttl_minutes: int = 60):
    """Maak een tijdelijk token aan voor een AI-agent met beperkte scope."""
    return jwt.encode({
        "sub": f"agent:{agent_id}",
        "tenant_id": tenant_id,
        "scope": scope,          # Specifieke rechten voor deze agent
        "role": "agent",         # Nieuw roltype, minimale rechten
        "exp": datetime.utcnow() + timedelta(minutes=ttl_minutes),
    }, settings.JWT_SECRET_KEY, algorithm="HS256")
```

---

## Prioritering voor ROADMAP

Op basis van de bovenstaande inzichten, aanbevolen volgorde:

| Prioriteit | Feature | Fase | Effort |
|-----------|---------|------|--------|
| Hoog | NIST AI RMF als normenkader | Fase 2 | Medium |
| Hoog | AI-systemenregister (EU AI Act) | Fase 2 | Medium |
| Medium | Agent-token type (NHI) | Fase 2 | Klein |
| Medium | AI Governance component in assessment | Fase 3 | Groot |
| Laag | Volledige NHI lifecycle management | Fase 3 | Groot |

---

## Referenties

- [NIST AI RMF 1.0](https://airc.nist.gov/RMF) — officieel document
- [CSA Cloud Controls Matrix](https://cloudsecurityalliance.org/research/cloud-controls-matrix/) — NHI-controls
- EU AI Act (Verordening 2024/1689) — art. 12 (logging), art. 14 (menselijk toezicht), art. 15 (cybersecurity)

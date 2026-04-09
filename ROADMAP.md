# Roadmap

## Huidige staat

Het GRC-platform is functioneel voor de inrichtingsmodus én dagelijks GRC-gebruik.

**Beschikbaar:**
- Inrichtingsmodus — 22 stappen door 4 fasen, volledig AI-ondersteund
- GRC-engine — risico's, controls, assessments, evidence, incidenten
- Multi-tenant architectuur met RBAC en Row Level Security
- AI-laag — 7 domeinagenten, RAG-pipeline op normatieve documenten (BIO 2.0, ISO 27001, ISO 27701, ISO 22301, AVG), AIAuditLog
- Docker-gebaseerde installatie

---

## Fase 2 — Productie-readiness

Klaar voor productie-gebruik bij gemeenten.

- [ ] HTTPS via Caddy reverse proxy (documentatie)
- [ ] Rate limiting op API-endpoints
- [ ] Geautomatiseerde backup-strategie PostgreSQL
- [ ] Monitoring en observability (Langfuse reeds ondersteund)
- [ ] Deployment-documentatie voor IT-beheerders
- [ ] Security hardening checklist

## Fase 3 — Samenwerken tussen organisaties

Schaalbaar naar meerdere organisaties en regio's.

- [ ] Regionaal dashboard — compliance-scores delen tussen gemeenten
- [ ] Governance-tooling voor centrumgemeente-constructies
- [ ] Uitgebreide rapportage-module
- [ ] Community-bijdragen: templates, aanpakken, best practices

---

## Bijdragen

Heb je ideeën, wil je een feature aanvragen of zelf bijdragen? Zie [CONTRIBUTING.md](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md) of open een [issue](https://github.com/security-commons-nl/grc-platform/issues).

# IMS Platform Features — Gedetailleerde Functionaliteit

> **Versie:** 2.0 — Februari 2026
> **Status:** Actueel (gebaseerd op code-inventarisatie)

Dit document beschrijft **alle gebouwde functionaliteit** van het IMS-platform, georganiseerd per domein. Voor architectuur en ontwerpbeslissingen, zie [COMPLETE_DESIGN_OVERVIEW.md](COMPLETE_DESIGN_OVERVIEW.md).

---

## Inhoudsopgave

1. [Risicobeheer (ISMS)](#1-risicobeheer-isms)
2. [Privacybeheer (PIMS/AVG)](#2-privacybeheer-pimsavg)
3. [Business Continuity (BCMS)](#3-business-continuity-bcms)
4. [Governance & Compliance](#4-governance--compliance)
5. [Assessments & Verificatie](#5-assessments--verificatie)
6. [Verbetering & Incidenten](#6-verbetering--incidenten)
7. [AI-systeem](#7-ai-systeem)
8. [Workflows & Automatisering](#8-workflows--automatisering)
9. [Integraties](#9-integraties)
10. [Rapportage & Dashboards](#10-rapportage--dashboards)
11. [Gebruikersbeheer & RBAC](#11-gebruikersbeheer--rbac)
12. [Multi-Tenancy & Shared Services](#12-multi-tenancy--shared-services)
13. [Frontend & UI](#13-frontend--ui)
14. [Entiteitenlijst](#14-entiteitenlijst)
15. [API-overzicht](#15-api-overzicht)

---

## 1. Risicobeheer (ISMS)

### 1.1 Risicoregister

**Pagina:** `/risks`
**API:** `/api/v1/risks`
**Entiteiten:** Risk, RiskTemplate, RiskThreatLink, ControlRiskLink

Elk risico wordt vastgelegd met:

| Veld | Beschrijving |
|------|--------------|
| **Titel & beschrijving** | Vrije tekst beschrijving van het risico |
| **Scope** | Gekoppeld aan organisatie-eenheid, proces of asset |
| **Inherente scores** | Kans (1-4) x Impact (1-4) = Score (1-16) — voor controls |
| **Residuele scores** | Kans x Impact na mitigerende maatregelen |
| **Kwetsbaarheidsscore** | 0-100, berekend als 100 - control_effectiveness_% |
| **Dreigingscategorie** | MAPGOOD-classificatie |
| **Aandachtskwadrant** | In Control-model: Mitigeren / Zekerheid / Monitoren / Accepteren |
| **Behandelstrategie** | Reduceren / Overdragen / Vermijden / Accepteren |
| **Overdrachtspartij** | Verplicht bij strategie "Overdragen" (Hiaat 4) |
| **Beleidsuitgangspunt** | Koppeling naar PolicyPrinciple (Hiaat 6) |
| **Verwerkingsactiviteit** | Koppeling naar ProcessingActivity (voor PIMS-risico's) |

**Frontend-functies:**
- **Interactieve 4x4 risicomatrix** — klik op cel om kans/impact te selecteren
- **Kwadranten-filter** — toon alleen risico's in specifiek kwadrant
- **Control-koppeling** — link en ontkoppel controls direct vanuit het risico
- **Desktop tabel + mobiele kaarten** — volledig responsive
- **Verwijder-bevestiging** — dialoog met risiconaam in rood

### 1.2 "In Control"-model

**Pagina:** `/in-control`
**API:** `/api/v1/in-control`
**Entiteit:** InControlAssessment (Hiaat 5)

Het "In Control"-model classificeert risico's op twee assen:

```
                     IMPACT
                Laag          Hoog
         ┌────────────┬────────────┐
  Hoog   │  MONITOR   │  MITIGATE  │
Kwets-   │  Meten,    │  Actief    │
baarheid │  wachten   │  aanpakken │
         ├────────────┼────────────┤
  Laag   │   ACCEPT   │ ASSURANCE  │
         │ Loslaten   │ Auditen,   │
         │            │ bewijzen   │
         └────────────┴────────────┘
```

**Per scope wordt beoordeeld:**
- **In control** — Alle requirements gedekt, controls effectief, geen kritieke bevindingen
- **Beperkt** — Gaps aanwezig, remediering in gang
- **Niet in control** — Kritieke gaps, ongeadresseerde bevindingen, verlopen acties

**Dashboard toont:**
- Scopekaarten met status-badge (groen/oranje/rood)
- Inline metrieken: open risico's, hoge/kritieke risico's, bevindingen, verlopen acties
- Klik-through naar scope-detail voor remediering

**Harde regel:** Risicoscore >= 9 met acceptatie vereist formeel DT-besluit (Decision).

### 1.3 MAPGOOD-dreigingsmodel

**Entiteiten:** Threat, ThreatActor, Vulnerability, RiskThreatLink

7 dreigingscategorieen (Nederlandse standaard):

| Letter | Categorie | Voorbeelden |
|--------|-----------|-------------|
| **M** | Menselijk falen | Fouten, social engineering, onbewust handelen |
| **A** | Applicatie falen | Software bugs, crashes, kwetsbaarheden |
| **P** | Proces falen | Procedurale fouten, ontbrekende stappen |
| **G** | Gegevens | Data-kwaliteit, integriteit, verlies |
| **O** | Omgeving | Brand, overstroming, stroomuitval |
| **O** | Opzet | Bewuste aanvallen, sabotage, hacking |
| **D** | Derden | Leveranciers, ketenpartners, outsourcing |

Dreigingen worden gekoppeld aan risico's via `RiskThreatLink` met:
- Gekoppelde vulnerability
- Gekoppelde threat actor (Script Kiddie, Organized Crime, Nation State, Insider, etc.)
- Impact-inschatting

### 1.4 Risicokader

**Pagina:** `/risk-framework`
**API:** `/api/v1/risk-framework`
**Entiteit:** RiskFramework (Hiaat 3)

Configureerbare schalen per tenant:

| Instelling | Beschrijving |
|------------|--------------|
| **Kansschaal** | Niveaunamen + percentages (Low, Medium, High, Critical) |
| **Impactschaal** | Niveaunamen + financiele ranges |
| **Groen-zone** | Risico's < X score: automatisch acceptabel |
| **Geel-zone** | Risico's X-Y score: monitoren |
| **Rood-zone** | Risico's > Y score: verplicht mitigeren |
| **Escalatiedrempel** | Score waarboven verplichte escalatie naar DT |

**Activering:** Een framework activeren maakt het tenant-breed de standaard. Slechts een actief framework per tenant.

### 1.5 Risk Appetite

**Entiteit:** RiskAppetite

Per tenant en per domein:
- **Overall appetite:** Risicomijdend / Minimaal / Voorzichtig / Gematigd / Open / Risicozoekend
- **Per domein:** ISMS, PIMS, BCMS, Financieel, Reputatie, Compliance
- **Auto-accept threshold:** Tot dit niveau automatisch accepteren
- **Escalation threshold:** Vanaf dit niveau verplicht escaleren
- **Max acceptable risk score:** Maximale residuele score (1-16)

### 1.6 Monte Carlo-simulatie

**Pagina:** `/simulation`
**API:** `/api/v1/simulation`

Kwantitatieve risicoanalyse:

**Configuratie:**
- Verdelingsmodel (uniform, normaal, driehoekig)
- Aantal iteraties (standaard 10.000)
- Scope-filter (welke risico's meenemen)

**Resultaten:**
- **Expected Loss** — Verwacht verlies
- **Value at Risk (VaR)** — 95e percentiel
- **Maximum / Minimum Loss** — Uitersten
- **Histogram** — Verdeling van uitkomsten
- **Tornado-diagram** — Top 10 risico-drivers (sensitivity analysis)
- **Export** als PDF of CSV

### 1.7 Besluitlog

**Pagina:** `/decisions`
**API:** `/api/v1/decisions`
**Entiteiten:** Decision, DecisionRiskLink (Hiaat 1)

Formele besluitregistratie voor IT-governance:

| Besluittype | Beschrijving |
|-------------|--------------|
| **Restrisico-acceptatie** | Bewust accepteren van een bekend risico |
| **Prioritering** | Prioriteren van mitigerende maatregelen |
| **Afwijking** | Tijdelijke uitzondering op een eis |
| **Scopewijziging** | Assets toevoegen/verwijderen uit scope |
| **Beleidsgoedkeuring** | Goedkeuren van beleidsdocument |

**Functies:**
- Motivering en voorwaarden vastleggen
- Geldigheidsduur met automatische verloop-signalering
- Koppeling aan een of meerdere risico's
- Status: Nieuw → Actief → Goedgekeurd → Verlopen
- Dashboard-waarschuwing bij verlopen besluiten

---

## 2. Privacybeheer (PIMS/AVG)

### 2.1 Verwerkingsregister (Art. 30)

**API:** `/api/v1/privacy`
**Entiteit:** ProcessingActivity

Volledig register conform AVG Art. 30:

| Veld | Beschrijving |
|------|--------------|
| **Doel** | Verwerkingsdoel |
| **Grondslag** | Toestemming / Overeenkomst / Wettelijke verplichting / Vitaal belang / Publieke taak / Gerechtvaardigd belang |
| **Betrokkenen** | Categorieen van betrokkenen |
| **Persoonsgegevens** | Welke gegevens worden verwerkt |
| **Bijzondere categorieen** | Art. 9: gezondheid, biometrie, etc. |
| **Ontvangers** | Wie ontvangt de gegevens |
| **Doorgifte** | Doorgifte buiten EU + waarborgen (SCCs, BCRs, adequaatheidsbesluit) |
| **Bewaartermijn** | Hoe lang worden gegevens bewaard |
| **DPIA vereist** | Automatische flagging bij hoog-risico verwerkingen |
| **Eigenaar** | Verantwoordelijke + review-cyclus |

### 2.2 Betrokkenenverzoeken (Art. 15-22)

**Entiteit:** DataSubjectRequest

Verzoektypes:
- **Inzage** (Art. 15) — Recht op informatie
- **Rectificatie** (Art. 16) — Recht op correctie
- **Wissing** (Art. 17) — Recht op vergetelheid
- **Beperking** (Art. 18) — Recht op verwerkingsbeperking
- **Dataportabiliteit** (Art. 20) — Recht op overdracht
- **Bezwaar** (Art. 21) — Recht op bezwaar

**Workflow:**
- Ontvangst met deadline (30 dagen, verlengbaar)
- Identiteitsverificatie (methode + datum)
- Toewijzing aan behandelaar
- Respons met methode en eventuele weigeringsreden
- Automatische deadline-herinneringen

### 2.3 Datalekmelding (Art. 33-34)

**Entiteit:** Incident (met GDPR-specifieke velden)

Bij een datalek worden vastgelegd:
- **Aantal betrokkenen** wiens gegevens geraakt zijn
- **Categorieen persoonsgegevens** die gelekt zijn
- **Bijzondere categorieen** betrokken (ja/nee)
- **AP-melding:** deadline 72 uur, referentienummer
- **Betrokkenen-notificatie:** datum, methode
- Koppeling naar verwerkingsactiviteit en continuiteitsplan

### 2.4 Verwerkersovereenkomsten (Art. 28)

**Entiteit:** ProcessorAgreement

Per overeenkomst:
- Leverancier (Scope/Supplier)
- Verwerkingsactiviteit
- Verwerkingsbeschrijving
- Sub-verwerkers toegestaan + lijst
- Beveiligingseisen
- Auditrechten
- Meldtermijn datalekken (in uren)

---

## 3. Business Continuity (BCMS)

### 3.1 Business Impact Analysis (BIA)

**API:** `/api/v1/assessments` (type: BIA)
**Entiteiten:** Assessment, AssessmentQuestion, AssessmentResponse, BIAThreshold

De BIA is een assessmenttype met automatische berekening:

**Vragenlijst:**
- 12 BIA-vragen verdeeld over 8 schalen
- Vraagtypen: Ja/Nee, Schaal 1-4/5/10, Tekst, Meerkeuze, Bestandsupload, Datum
- Per vraag: gewicht, categorie, volgorde, slaag-antwoord

**Automatische berekening (bij fase "Afgerond"):**
1. Responses → CIA-scores berekenen (Vertrouwelijkheid, Integriteit, Beschikbaarheid, elk 1-4)
2. RTO berekenen met RTO-modifier
3. RPO berekenen
4. BIAThreshold lookup → uren + plan-vereiste
5. **Terugschrijving naar Scope:** C/I/A-ratings, RTO/RPO/MTPD uren
6. CIA-label instellen (bijv. "C3-I2-A4")
7. BCP-vereiste flag zetten

**BIA-drempels (BIAThreshold):**
- Score 1-4 → classificatieniveau, label, RTO/RPO/MTPD uren
- Tenant-specifiek of globale defaults
- Bepaalt of continuiteitsplan verplicht is

### 3.2 Continuiteitsplannen

**API:** `/api/v1/continuity`
**Entiteit:** ContinuityPlan

Plantypen:
- **BCP** — Business Continuity Plan
- **DRP** — Disaster Recovery Plan
- **Crisismanagement** — Crisis Management Plan
- **Communicatie** — Crisis Communication Plan
- **IT Recovery** — IT Recovery Plan

Per plan:
- Status (Concept / Review / Goedgekeurd / Gepubliceerd / Gearchiveerd)
- Activeringstriggers
- Activeringsautoriteit
- Crisisteam (JSON)
- Laatste test, laatste review, volgende review

### 3.3 Continuiteitstesten

**Entiteit:** ContinuityTest

Testtypen:
- **Tabletop** — Papieren oefening
- **Walkthrough** — Stap-voor-stap doorloop
- **Simulatie** — Gesimuleerde verstoring
- **Full Interruption** — Volledige onderbreking
- **Component Test** — Test van individueel component

Per test:
- Scenario, deelnemers, duur
- Doelen behaald (ja/nee)
- Resultaten, geleerde lessen, geidentificeerde verbeteringen
- Koppeling naar Assessment (voor PDCA-cyclus)

---

## 4. Governance & Compliance

### 4.1 Standaarden & Requirements

**Pagina:** `/frameworks`
**API:** `/api/v1/standards`
**Entiteiten:** Standard, Requirement, RequirementMapping

**Ondersteunde frameworks:**
BIO, ISO 27001:2022, ISO 27002, ISO 27701, ISO 22301, AVG/GDPR, NEN 7510, NIST CSF, CIS Controls

**Per standaard:** naam, versie, categorie, meertalig (NL/EN)
**Per requirement:** code, titel, beschrijving, categorie, standaard-koppeling

### 4.2 Rosetta Stone (Cross-Framework Mapping)

**Entiteit:** RequirementMapping

Automatische mapping tussen frameworks met:
- **Mappingtypen:** Equivalent, Subset, Superset, Related
- **AI-confidence score** (0-1) voor AI-gegenereerde mappings
- **Notities** voor handmatige toelichting

**Voorbeeld:** ISO 27001 A.5.1 ↔ BIO 5.1.1 (confidence: 0.95)

### 4.3 Statement of Applicability (SoA)

**Pagina:** `/compliance`
**API:** `/api/v1/soa`
**Entiteit:** ApplicabilityStatement

Per SoA-entry:
- Requirement + Scope combinatie
- **Toepasselijkheid:** Ja/Nee + motivering
- **Implementatiestatus:** Planned / In Progress / Implemented / Approved
- **Dekkingstype:** Lokaal / Gedeeld / Gecombineerd / Niet gedekt / N.v.t.
- Lokale control en/of gedeelde control
- Bij gedeelde control: adequaatheidsbeoordeling door consumer
- Gap-beschrijving en compenserende controls

**Frontend-functies:**
- Voortgangsbalk met compliance %
- Filteren op scope, standaard, dekkingstype, status
- SoA initialiseren vanuit standaard (bulk-creatie van entries)
- Statistiekkaarten: totaal, geimplementeerd, in uitvoering, gaps

### 4.4 Beleid

**Pagina:** `/policies`
**API:** `/api/v1/policies`
**Entiteiten:** Policy, PolicyPrinciple

**Beleidsworkflow:**
```
Concept → In Review → Goedgekeurd → Gepubliceerd → Gearchiveerd
```

Per beleid: titel, inhoud, versie, status, goedkeuring.

### 4.5 Beleidsuitgangspunten (Hiaat 6)

**Pagina:** `/policy-principles`
**API:** `/api/v1/policy-principles`
**Entiteit:** PolicyPrinciple

Traceerbare keten: **Beleid → Principe → Risico → Control**

Per principe:
- Titel en beschrijving
- Gekoppelde beleidsdocumenten
- Gekoppelde requirements
- Visualisatie van de traceerbaarheidsketen

### 4.6 Management Review

**API:** `/api/v1/reports` (als onderdeel van management-cyclus)
**Entiteit:** ManagementReview

Conform ISO 27001 §9.3 en ISO 22301 §9.3:

**Inputs:**
- Status vorige acties
- Contextwijzigingen
- Non-conformiteiten samenvatting
- Open/gesloten bevindingen
- KPI-samenvatting
- Auditresultaten
- Doelstellingenstatus
- Feedback stakeholders
- Risicobeoordeling
- Kritieke risico's, incidenten, datalekken

**Outputs:**
- Verbeterbeslissingen
- Systeemwijzigingen
- Resourcebeslissingen
- Conclusies + actie-items
- Volgende review-datum

### 4.7 Jaarplanning

**Entiteit:** CompliancePlanningItem

Itemtypen: Internal Audit, External Audit, Certificering, Hercertificering, Management Review, Risicobeoordeling, BIA, Pentest, Compliance Check, Leveranciersaudit, DPIA

Per item: planning-jaar, geplande/werkelijke start- en einddatum, verantwoordelijke, externe partij, geschatte/werkelijke dagen en kosten.

### 4.8 Doelstellingen & KPI's

**Entiteiten:** Objective, ObjectiveKPI, KPIMeasurement

Conform ISO 27001 §6.2:

**Per doelstelling:**
- Domein (ISMS, PIMS, BCMS, Geintegreerd)
- Vereiste acties en resources
- Eigenaar, streefdatum, status
- Gerelateerde risico's, voortgang %

**Per KPI:**
- Metrieknaam, eenheid, streefwaarde, richting (lager/hoger)
- Drempels: groen/oranje/rood
- Huidige waarde en trend (Verbeterend / Stabiel / Dalend)
- Meetfrequentie, databron, geautomatiseerd

**Per meting:**
- Waarde, meetdatum, periode
- Gemeten door, databron

---

## 5. Assessments & Verificatie

### 5.1 Assessmenttypes

**Pagina:** `/assessments` + `/assessments/[id]`
**API:** `/api/v1/assessments`
**Entiteiten:** Assessment, AssessmentQuestion, AssessmentResponse, Evidence, Finding

| Type | Icoon | Beschrijving |
|------|-------|-------------|
| **DPIA** | Shield (paars) | Data Protection Impact Assessment |
| **Pentest** | Bug (rood) | Penetratietest |
| **Audit** | Clipboard (blauw) | Interne of externe audit |
| **Self-Assessment** | User-check (groen) | Zelfevaluatie (bijv. ENSIA) |
| **BIA** | Shield-check (oranje) | Business Impact Analysis |
| **Compliance Journey** | Route (cyaan) | Compliance-traject |
| **Supplier Assessment** | Truck (amber) | Leveranciersbeoordeling |
| **Maturity Assessment** | Trending-up (teal) | Volwassenheidsmeting |

### 5.2 7-Fasen Workflow

```
Aangevraagd → Planning → Voorbereiding → In uitvoering → Review → Rapportage → Afgerond
```

**Visuele stepper** bovenaan de detailpagina:
- Afgeronde fasen: groene cirkel met vinkje
- Huidige fase: blauwe cirkel met nummer
- Toekomstige fasen: grijze cirkel
- Klikbaar om fase te laten voortgang (indien toegestaan)

### 5.3 Assessment-detailpagina (5 tabs)

**Tab 1: Overzicht**
- Assessment-metadata (type, scope, lead assessor, deadline)
- BIA-resultaatkaart (indien BIA): CIA-classificatie, RTO, RPO, kostenschatting

**Tab 2: Vragenlijst**
- Dynamische vragenlijst (alleen bij BIA/Self-Assessment)
- Vraagtypen: Ja/Nee, Schaal, Tekst, Meerkeuze, Bestandsupload, Datum
- Voortgangsindicator: "X / Y vragen beantwoord"
- BIA-berekeningsknop met spinner

**Tab 3: Bevindingen**
- Lijst van bevindingen met ernst-badge (Low/Medium/High/Critical)
- Aanmaken, bewerken, sluiten van bevindingen
- Sluiten vereist afgeronde correctieve actie (Hiaat 7)

**Tab 4: Evidence**
- Bewijsstukken gekoppeld aan het assessment
- Types: Document, Screenshot, Log, Report, Config
- AI-analyse mogelijkheid (Pass/Fail/Partial)

**Tab 5: Acties (Correctieve acties)**
- Acties per bevinding
- Toewijzing aan gebruiker met deadline
- Prioriteit (Hoog/Midden/Laag) en status
- Markeer als afgerond met notities

### 5.4 Maturity Assessment

**Entiteiten:** MaturityAssessment, MaturityDomainScore

Niveaus (CMMI-gebaseerd):
1. **Incomplete** — Niet aanwezig
2. **Initial** — Ad hoc, ongecontroleerd
3. **Managed** — Gepland en gevolgd
4. **Defined** — Gestandaardiseerd
5. **Quantitatively Managed** — Gemeten en gecontroleerd
6. **Optimizing** — Continue verbetering

Per domein (12 domeinen: ISMS, PIMS, BCMS, Risicobeheer, Assetbeheer, Toegangsbeheer, Cryptografie, Fysieke beveiliging, Operations, Communicatie, Incidentbeheer, Compliance):
- Huidig niveau, streefniveau, gap
- Prioriteit, motivering, bewijssamenvatting, aanbevelingen

---

## 6. Verbetering & Incidenten

### 6.1 Bevindingen & Issues

**Entiteiten:** Finding, Issue

**Bevinding (Finding):**
- Ontstaat uit assessment of incident
- Ernst: Low / Medium / High / Critical
- Gekoppeld aan control en/of requirement
- `is_incidental` flag: true = eenmalig, false = structureel (gelinkt aan Issue)

**Issue (Structureel probleem):**
- Groepeert gerelateerde bevindingen/incidenten
- Type: Technical, Functional, Process, Tool, AI, Other
- Root cause analyse, bijdragende factoren
- Opgelost door + datum

### 6.2 Correctieve Acties

**Entiteit:** CorrectiveAction

Per actie:
- Gekoppeld aan finding, incident, of issue
- Type: Preventief / Correctief / Detectief
- Toegewezen aan gebruiker met deadline
- Prioriteit: Critical / High / Medium / Low
- Status + verificatie
- Kan resulteren in nieuwe control (`control_created_id`)
- Externe systeem-koppeling (TopDesk, ServiceNow)

**ACT-feedbackloop (Hiaat 7):**
- Dashboard-waarschuwing toont:
  - Aantal geblokkeerde bevindingen (wachten op actie-afronding)
  - Aantal bevindingen zonder correctieve acties
- API: `/api/v1/assessments/act-overdue`

### 6.3 Incidenten

**Pagina:** `/incidents`
**API:** `/api/v1/incidents`
**Entiteit:** Incident

Per incident:
- Titel, beschrijving, ernst (Low/Medium/High/Critical/Observation)
- Status: Nieuw → In behandeling → Vervallen → Opgelost
- Datum voorkomen, gedetecteerd, opgelost
- Impact, root cause, resolutie
- **Datalek flag** met GDPR-specifieke velden (zie sectie 2.3)
- Koppeling naar scope, issue, continuiteitsplan, verwerkingsactiviteit
- Externe systeem-koppeling
- `IncidentControlLink` — welke controls faalden

### 6.4 Uitzonderingen (Waivers)

**Entiteit:** Exception

Formele afwijking van een requirement:
- Titel, motivering, geaccepteerd risiconiveau
- Compenserende controls
- Aanvraagdatum, goedkeuringsdatum, verloopdatum
- Status, aanvrager, goedkeurder
- Gekoppeld aan scope, requirement, risico

### 6.5 Gap-analyse

**Entiteit:** GapAnalysis, GapAnalysisItem

Bij standaard-versiewijzigingen (bijv. ISO 27001:2013 → 2022):
- Automatische mapping van oude → nieuwe requirements
- Gap-identificatie per requirement
- Inspanningsschattingen
- AI-analyse samenvatting

### 6.6 Verbeterinitiatieven

**Entiteiten:** Initiative, InitiativeMilestone

Grotere verbeterprojecten:
- Business case, prioriteit, sponsor, eigenaar, team
- Status: Idee → Voorgesteld → Goedgekeurd → In uitvoering → Afgerond
- Voortgang %, statusnotities
- Mijlpalen met geplande/werkelijke datums, deliverables, bewijs
- Verwachte en werkelijke uitkomsten, geleerde lessen
- Trigger: management review, risico, bevinding, of incident
- Externe systeem-koppeling

### 6.7 Backlog

**Pagina:** `/backlog`
**API:** `/api/v1/backlog`
**Entiteit:** BacklogItem

Verbeterideeeen en feature requests:
- User story format: "Als [rol] wil ik [functie] zodat [voordeel]"
- Type: Technical / Functional / Process / Tool / AI / Other
- Prioriteit (admin-gestuurd), status, stemmen
- Ingediend door (naam), admin-notities

---

## 7. AI-systeem

### 7.1 Architectuur

```
Chat Island (altijd zichtbaar) → Agent Orchestrator → Domein Agent → Tools → API/Knowledge
```

**Multi-provider fallback:**
1. **Mistral** (primair) — Frankrijk, EU
2. **Scaleway** (fallback) — Frankrijk, EU
3. **Ollama** (lokaal offline) — Localhost

Configureerbaar via `AI_PROVIDER_PRIORITY`, `AI_TIMEOUT`.

### 7.2 19 AI-agenten

#### Domeinagenten (11)

| Agent | Domein | Expertise |
|-------|--------|-----------|
| **RiskAgent** | Risicobeheer | In Control-model, MAPGOOD, classificatie, behandelstrategieen |
| **MeasureAgent** | Controls | Maatregelontwerp, effectiviteit, traceerbaarheid |
| **ComplianceAgent** | Governance | Frameworks, requirements, SoA, gap-analyse, Rosetta Stone |
| **PolicyAgent** | Beleid | Beleidsdrafting, principes, goedkeuringsworkflows |
| **PrivacyAgent** | PIMS/AVG | Verwerkingen, DPIA, betrokkenenrechten |
| **BCMAgent** | Continuiteit | BIA, RTO/RPO, continuiteitsplannen, tests |
| **IncidentAgent** | Incidenten | Incidentafhandeling, root cause analyse, datalekmelding |
| **ImprovementAgent** | Verbetering | Correctieve acties, initiatieven, geleerde lessen |
| **AssessmentAgent** | Verificatie | Assessment planning, BIA-berekening, fasen-workflow |
| **ScopeAgent** | Scope | Hierarchy, afhankelijkheden, governance status |
| **SupplierAgent** | Leveranciers | Third-party risico, verwerkersovereenkomsten |

#### Managementagenten (3)

| Agent | Domein | Expertise |
|-------|--------|-----------|
| **PlanningAgent** | Planning | Jaarplanning, audit scheduling, certificeringstijdlijnen |
| **ObjectivesAgent** | Doelstellingen | ISO 27001 §6.2 objectives, KPI-tracking |
| **MaturityAgent** | Volwassenheid | CMMI-assessments, niveau-tracking, verbeterroadmaps |

#### Systeemagenten (5)

| Agent | Domein | Expertise |
|-------|--------|-----------|
| **WorkflowAgent** | Workflows | Transities, goedkeuringen, SLA-monitoring |
| **ReportAgent** | Rapportage | Rapportgeneratie, dashboard-ontwerp |
| **DashboardAgent** | Dashboards | AI-gegenereerde dashboard-layouts |
| **AdminAgent** | Beheer | Gebruikers, rollen, configuratie |
| **OnboardingAgent** | Onboarding | Organisatieprofiel wizard, framework-selectie |

### 7.3 Tool-systeem

Elke agent heeft toegang tot gespecialiseerde tools:

| Categorie | Beschrijving | Voorbeeld |
|-----------|--------------|-----------|
| **read** | Data ophalen (geen side effects) | `list_risks()`, `get_requirement_mappings()` |
| **write** | Aanmaken/wijzigen/verwijderen | `create_control()`, `move_policy_state()` |
| **knowledge** | RAG-zoeken | `search_knowledge_tool()` |
| **external** | Externe API's aanroepen | Toekomstig: TopDesk, ServiceNow |
| **utility** | Helperfuncties | Berekeningen, formatting |

**Governance:** Tools met `requires_confirmation=true` vereisen gebruikersbevestiging. Alle tool-uitvoeringen worden gelogd in `AIToolExecution`.

### 7.4 Suggestiesysteem

**Entiteit:** AISuggestion

AI genereert suggesties die gebruikers accepteren of afwijzen:

| Fase | Beschrijving |
|------|--------------|
| **Suggestion** | AI maakt voorstel met confidence score (0-1) en reasoning |
| **Review** | Gebruiker bekijkt suggestie |
| **Decision** | Accepteren / Aanpassen / Afwijzen (met verplichte motivering) |
| **Audit** | Volledige trail van alle AI-interacties |

Suggestietypes: field_update, create_entity, workflow_transition, classification

### 7.5 RAG-kennisbank

**Entiteiten:** AIKnowledgeBase, KnowledgeArtifact

**AIKnowledgeBase:**
- Platform-, methodologie-, framework-, best practice-, terminologie-kennis
- Glossary met termen en aliassen
- Context-aware: `applicable_contexts`, `applicable_entity_types`
- pgvector embeddings voor semantisch zoeken
- Tenant-specifiek of globaal

**KnowledgeArtifact:**
- Ruwe kennis voor RAG: interviews, uploads, websites
- Verificatieworkflow: Unverified → Pending Approval → Verified / Rejected
- Gekoppeld aan scope

### 7.6 Chat Island

**Frontend-component:** Minimaliseerbaar chatpaneel rechtsonder

Functies:
- Automatische agent-detectie op basis van huidige pagina
- Handmatige agent-selectie via dropdown
- Context passing (huidige entiteit, paginanaam)
- Gespreksgeschiedenis
- Typing-indicator

---

## 8. Workflows & Automatisering

### 8.1 Generiek Workflowsysteem

**API:** `/api/v1/workflows`
**Entiteiten:** WorkflowDefinition, WorkflowState, WorkflowTransition, WorkflowInstance, WorkflowStepHistory

Elk proces kan een workflow hebben:

```
WorkflowDefinition
  ├── WorkflowState (1..n)
  │     • is_initial, is_final, is_rejection
  │     • allowed_roles, expected_duration_days
  │     • ai_guidance_prompt, ai_validation_prompt
  │
  └── WorkflowTransition (1..n)
        • from_state → to_state
        • requires_approval, approver_roles
        • conditions (JSON)
        • ai_pre_validation_enabled
        • ai_approval_summary_enabled
```

### 8.2 AI bij Workflows

| Moment | AI-functie |
|--------|------------|
| **Bij state entry** | Guidance: "Wat moet ik hier doen?" |
| **Voor transitie** | Validatie: "Is alles compleet voor deze stap?" |
| **Bij goedkeuring** | Samenvatting: overzicht voor approver |
| **Na afwijzing** | Suggesties: verbeteradviezen |
| **Voortgang** | Predictie: verwachte afrondingsdatum + blokkades |

### 8.3 Workflow Instance Tracking

Per actieve workflow:
- Huidige state, status, deadline
- Toegewezen aan, huidige approver
- Stappen afgerond / resterend
- AI-guidance, geidentificeerde issues, completion confidence
- Volledige stap-historie (wie, wanneer, duur, AI-validatie resultaat)

### 8.4 Escalatie

Automatische escalatie wanneer:
- Stap de verwachte duur overschrijdt (`escalation_after_days`)
- Deadline nadert zonder actie
- AI issues identificeert die blokkade veroorzaken

---

## 9. Integraties

### 9.1 Externe Systemen

**API:** `/api/v1/sync`, `/api/v1/webhooks`
**Entiteiten:** IntegrationConfig, IntegrationSyncLog

| Systeem | Richting | Wat wordt gesynchroniseerd |
|---------|----------|---------------------------|
| **TopDesk** | Bi-directioneel | Incidenten, correctieve acties, changes |
| **ServiceNow** | Bi-directioneel | Incidenten, changes, gebruikers |
| **Proquro** | Inbound | Compliance assessments |
| **BlueDolphin** | Inbound | Risicomanagement data |

### 9.2 Sync-configuratie

Per integratie:
- Base URL, API-versie, authenticatie (API key / OAuth2)
- Sync-richting: inbound / outbound / bi-directioneel
- Sync-frequentie (minuten)
- Veld-mapping (JSON)
- Status: Active / Inactive / Error / Pending Setup
- Sync-log met aantallen verwerkt/aangemaakt/bijgewerkt/gefaald

### 9.3 External References

Entiteiten met externe systeem-koppeling:
- **Scope:** external_id, external_source
- **Control:** external_system, external_reference, external_id, external_url
- **Incident:** external_system, external_reference, external_id, last_synced
- **CorrectiveAction:** external_system, external_reference, external_url
- **Initiative:** external_system, external_reference, external_url

---

## 10. Rapportage & Dashboards

### 10.1 Executive Dashboard

**Pagina:** `/reports`

KPI-kaarten (6-koloms grid):
1. **Totaal Risico's** — met "X Hoog/Kritiek" subtitle
2. **Compliance %** — overall compliance score
3. **Open Incidenten** — laatste 30 dagen
4. **Beleidsdocumenten** — "Y Gepubliceerd"
5. **Actieve Maatregelen** — "Effectiviteit: Z%"
6. **Frameworks** — "X Toepasselijk"

Plus: risicokwadrant-verdeling, compliance per framework, assessment-voortgang, incidenttrends.

### 10.2 Dashboard (Homepage)

**Pagina:** `/`

- Welkomstbanner met gebruikersnaam
- **PDCA Journey-widget** — 4-ring visuele stepper
- **ACT-feedbackloop waarschuwing** (oranje callout)
- **Statistiekkaarten:** Totaal Risico's, Te Mitigeren, Zekerheid, Geaccepteerd
- **Mijn Taken** — tabel met: goedkeuringen, correctieve acties, reviews
- **Risk Heatmap** — 4-kwadranten gekleurde matrix
- **Quick Actions:** Nieuw Risico, Start Assessment, Meld Incident

### 10.3 Rapporttemplates & Scheduling

**Entiteiten:** ReportTemplate, ScheduledReport, ReportExecution

- Templatetypen: compliance, risico, incident, management review, custom
- Outputformaten: PDF, Excel, Word, HTML
- Scheduling: dagelijks, wekelijks, maandelijks, kwartaal, jaarlijks, on-demand
- Ontvangers (JSON), e-mail verzending
- Generatie-audit trail

### 10.4 Relatiegrafiek

**Pagina:** `/relaties`
**API:** `/api/v1/graph`

Interactieve entity-relatie visualisatie:
- Nodes: Risk, Control, Scope, Measure, Decision, Assessment
- Edges: links, mitigates, implements, affects
- Kleurcodering per entity-type
- Hover voor details, klik voor navigatie
- Filter op entity-type, scope, relatietype
- Export als PNG/SVG/CSV

---

## 11. Gebruikersbeheer & RBAC

### 11.1 Drie-Lijnen Model

**Pagina:** `/users`
**API:** `/api/v1/users`
**Entiteiten:** User, UserScopeRole

| Rol | Lijn | Bevoegdheden |
|-----|------|-------------|
| **Beheerder** | - | Systeembeheer, gebruikersbeheer, volledige toegang |
| **Coordinator** | 2e lijn | Procescoordinatie, cross-domein, overzicht |
| **Eigenaar** | 1e lijn | Scope/domein-eigenaar, beleidsgoedkeuring |
| **Medewerker** | 1e lijn | Data-invoer, operationeel werk |
| **Toezichthouder** | 3e lijn | Read-only, assurance, audit |

### 11.2 Scope-Based RBAC

Rollen worden toegewezen **per scope**:
- Een gebruiker kan "Eigenaar" zijn van Scope A en "Medewerker" van Scope B
- `UserScopeRole` linkt: User ↔ Scope ↔ Rol met geldigheidsdatums
- API enforceert RBAC via decorators: `require_editor`, `require_oversight`, `require_admin`

### 11.3 Frontend-permissies

| Permissie | Controleert |
|-----------|------------|
| `is_admin` | Systeembeheer, BEHEER-sectie zichtbaar |
| `can_edit` | CRUD op operationele items |
| `can_configure` | INRICHTEN-sectie zichtbaar (scopes, beleid, assets) |
| `can_manage_users` | Gebruikersbeheer zichtbaar |

### 11.4 Administratie

**Pagina:** `/admin`

4 tabs:
1. **Overzicht** — Gebruikersstatistieken (totaal, actief, admin, inactief)
2. **Wachtwoordbeheer** — Reset wachtwoorden voor gebruikers
3. **Systeemstatus** — Healthchecks (database, API, AI, cache, storage) + uptime
4. **Auditlog** — Login-geschiedenis met IP-adres, status, filtering

---

## 12. Multi-Tenancy & Shared Services

### 12.1 Tenantmodel

**Entiteiten:** Tenant, TenantUser, TenantRelationship

```
SSC Bedrijfsvoering (is_service_provider: true)
  │
  TenantRelationship (SHARED_SERVICES)
  │
  ├── Gemeente Amsterdam
  ├── Gemeente Rotterdam
  └── Gemeente Den Haag
```

### 12.2 Shared Controls

**Entiteit:** SharedControl

1. **Provider-tenant** (SSC) maakt controls en markeert als gedeeld
2. **Consumer-tenant** ziet gedeelde controls in SoA
3. Consumer beoordeelt adequaatheid (`shared_control_adequate`)
4. Consumer kan lokale compenserende control toevoegen

### 12.3 Dekkingstype in SoA

| Type | Betekenis |
|------|-----------|
| **Lokaal** | Eigen control |
| **Gedeeld** | Centrale control van provider |
| **Gecombineerd** | Zowel lokaal als gedeeld |
| **Niet gedekt** | Geen control aanwezig |
| **N.v.t.** | Requirement niet van toepassing |

---

## 13. Frontend & UI

### 13.1 Technologie

- **Framework:** Reflex 0.5+ (Python → React/Vite)
- **Styling:** Radix UI + CSS
- **Thema:** Light/Dark mode (Indigo accent, Slate gray)
- **Taal:** Volledig Nederlands
- **Responsive:** Desktop tabel + Mobiele kaarten via breakpoints

### 13.2 Design Patterns

| Pattern | Implementatie |
|---------|---------------|
| **Responsive** | `rx.breakpoints(initial="none", md="block")` — tabellen desktop, kaarten mobiel |
| **CRUD Dialogen** | `rx.dialog.root` met form, error callout, actieknoppen |
| **Status Badges** | Kleurgecodeerd: groen (succes), rood (fout), oranje (waarschuwing), blauw (info) |
| **Lege Status** | Groot icoon + bericht + CTA-knop |
| **Loading** | Spinner + disabled knoppen tijdens async operaties |
| **Foutafhandeling** | Callout (pagina-niveau) of toast (snelle feedback) |
| **Bevestiging** | Dialoog bij destructieve acties (verwijderen) |

### 13.3 Componenten

| Component | Functie |
|-----------|---------|
| **Layout** | Paginawrapper met responsive sidebar, top bar, auth guard |
| **Risk Heatmap** | 4-kwadranten matrix met interactie |
| **Chat Island** | Minimaliseerbaar AI-chatpaneel |
| **PDCA Ring** | 4-ring visuele PDCA-stepper |
| **Journey Stepper** | 7-staps onboarding voortgang |
| **Relationship Graph** | Interactieve entity-relatie visualisatie |
| **Deadline** | Countdown timer met status-indicator |

### 13.4 Organisatieprofiel Wizard

**Pagina:** `/organization`
**6 stappen:**

1. **Identiteit** — Organisatietype, sector, werknemers, geografische scope
2. **Governance** — Frameworks, risk appetite, certificeringen
3. **IT-Landschap** — Cloud-strategie, datacenters, applicatieplatformen
4. **Privacy** — AVG-verwerking, datacategorieen, FG aanwezig
5. **Continuiteit** — RTO, RPO, downtime-tolerantie, bedrijfskritikaliteit
6. **Mensen** — Trainingsfrequentie, bewustzijnsniveau, personeelsbeleid

Na voltooiing: profiel in accordion-kaarten met per-sectie bewerking.

---

## 14. Entiteitenlijst

### Totaaloverzicht (85+ entiteiten per domein)

| Domein | Entiteiten |
|--------|-----------|
| **Multi-Tenancy (7)** | Tenant, TenantUser, TenantRelationship, SharedControl, SharedScope, VirtualScopeMember, AccessRequest |
| **Users & Access (2)** | User, UserScopeRole |
| **Governance (6)** | Standard, Requirement, RequirementMapping, Policy, PolicyPrinciple, OrganizationContext |
| **Organisatieprofiel (1)** | OrganizationProfile |
| **Scope (2)** | Scope, ScopeDependency |
| **Risicobeheer (9)** | Risk, RiskTemplate, RiskThreatLink, RiskFramework, RiskAppetite, ControlRiskLink, ThreatActor, Threat, Vulnerability |
| **Controls (3)** | Measure, Control, ControlMeasureLink |
| **Assessment (5)** | Assessment, AssessmentQuestion, AssessmentResponse, Evidence, BIAThreshold |
| **Verbetering (4)** | Finding, Issue, CorrectiveAction, GapAnalysis |
| **Privacy (3)** | ProcessingActivity, DataSubjectRequest, ProcessorAgreement |
| **BCM (2)** | ContinuityPlan, ContinuityTest |
| **Incidenten (2)** | Incident, Exception |
| **Management (5)** | Decision, DecisionRiskLink, ManagementReview, CompliancePlanningItem, InControlAssessment |
| **Doelstellingen (3)** | Objective, ObjectiveKPI, KPIMeasurement |
| **Initiatieven (3)** | Initiative, InitiativeMilestone, BacklogItem |
| **Workflows (5)** | WorkflowDefinition, WorkflowState, WorkflowTransition, WorkflowInstance, WorkflowStepHistory |
| **Documenten (4)** | Document, Attachment, Comment, Notification |
| **Audit (3)** | AuditLog, ReviewSchedule, Tag + EntityTag |
| **AI System (10)** | AIAgent, AITool, AIAgentToolAccess, AIToolExecution, AIConversation, AIConversationMessage, AISuggestion, AIKnowledgeBase, AIPromptTemplate, KnowledgeArtifact |
| **AI Support (1)** | Dashboard |
| **Rapporten (3)** | ReportTemplate, ScheduledReport, ReportExecution |
| **Integraties (2)** | IntegrationConfig, IntegrationSyncLog |
| **Instellingen (2)** | SystemSetting, TenantSetting |
| **SoA (1)** | ApplicabilityStatement |
| **Maturity (2)** | MaturityAssessment, MaturityDomainScore |

---

## 15. API-overzicht

### 32 Router-registraties

```
/api/v1/
├── /auth                      — Authenticatie (login, JWT)
├── /standards                 — Frameworks en standaarden
├── /policies                  — Beleidsdocumenten
├── /policy-principles         — Beleidsuitgangspunten (Hiaat 6)
├── /scopes                    — Scopehierarchie en governance (Hiaat 2)
├── /risks                     — Risicoregister (In Control-model)
├── /risk-framework            — Risicokader (Hiaat 3)
├── /in-control                — In-control status (Hiaat 5)
├── /decisions                 — Besluitlog (Hiaat 1)
├── /measures                  — Maatregelencatalogus
├── /controls                  — Control-implementaties
├── /users                     — Gebruikers en RBAC
├── /assessments               — Assessments, BIA, bevindingen, evidence
├── /incidents                 — Incident- en datalekbeheer
├── /privacy                   — AVG: verwerkingen, DSR, overeenkomsten
├── /continuity                — BCMS: plannen en testen
├── /soa                       — Statement of Applicability
├── /agents                    — AI-agenten en conversaties
├── /knowledge                 — Kennisbank (RAG)
├── /workflows                 — Workflow-automatisering
├── /reports                   — Rapporttemplates en scheduling
├── /dashboard                 — Dashboard-generatie
├── /backlog                   — Verbeterbacklog
├── /tenants                   — Tenantbeheer
├── /documents                 — Documentbeheer
├── /webhooks                  — Webhook-registratie
├── /sync                      — Externe systeem-sync
├── /organization-profile      — Onboarding wizard
├── /system                    — Systeembeheer
├── /graph                     — Entity-relatiegrafiek
└── /simulation                — Monte Carlo-simulatie
```

### Standaard CRUD-patroon

```
GET    /endpoint/                — Lijst (paginering, filters)
POST   /endpoint/                — Aanmaken
GET    /endpoint/{id}            — Ophalen
PATCH  /endpoint/{id}            — Bijwerken
DELETE /endpoint/{id}            — Verwijderen
```

### Gespecialiseerde Operaties

| Endpoint | Beschrijving |
|----------|-------------|
| `POST /risks/{id}/accept` | Formele risicoacceptatie |
| `PATCH /risks/{id}/quadrant` | Aandachtskwadrant instellen |
| `POST /risks/{id}/controls/{control_id}` | Control koppelen aan risico |
| `POST /assessments/{id}/advance-phase` | Assessment naar volgende fase |
| `POST /assessments/{id}/calculate-bia` | BIA-berekening triggeren |
| `POST /findings/{id}/close` | Bevinding sluiten (vereist afgeronde actie) |
| `POST /corrective-actions/{id}/complete` | Actie markeren als afgerond |
| `POST /policies/{id}/approve` | Beleid goedkeuren |
| `POST /policies/{id}/publish` | Beleid publiceren |
| `POST /scopes/{id}/governance` | Governance-status bijwerken |
| `POST /incidents/{id}/resolve` | Incident oplossen |
| `POST /dsr/{id}/verify-identity` | Identiteit betrokkene verifieren |
| `POST /dsr/{id}/respond` | Betrokkenenverzoek beantwoorden |
| `POST /decisions/{id}/expire` | Besluit laten verlopen |
| `POST /continuity/plans/{id}/activate` | Continuiteitsplan activeren |
| `POST /workflows/instances/{id}/transition` | Workflow-transitie uitvoeren |
| `POST /chat` | AI-conversatie starten |
| `POST /suggestions/{id}/accept` | AI-suggestie accepteren |
| `POST /suggestions/{id}/reject` | AI-suggestie afwijzen |
| `POST /reports/{id}/generate` | Rapport on-demand genereren |
| `GET /knowledge/search` | Kennisbank doorzoeken (RAG) |
| `GET /assessments/act-overdue` | ACT-feedbackloop dashboard |
| `GET /graph/relationships` | Entity-relaties ophalen |
| `POST /simulation/run` | Monte Carlo-simulatie starten |

---

*Einde document — Laatste update: Februari 2026*

# Gap-analyse: IMS Handboek (concept) vs. IMS Tooling datamodel

> **Bron handboek**: `IMS - handboek (concept).docx` (Gemeente Leiden, Integrated Management System — General)
> **Bron datamodel**: `X:\ARCHIEF\IMS` — FastAPI/SQLModel backend, 90+ entiteiten, 19 migraties
> **Datum analyse**: februari 2026

---

## Leeswijzer

Dit document vergelijkt wat het IMS-handboek beschrijft met wat de tooling ondersteunt. Per item is een actieplan opgenomen. De indeling is:

- **✅ Gedekt** — handboek en tooling zijn in lijn
- **⚠️ Gedeeltelijk** — concept aanwezig maar onvolledig of niet expliciet gemodelleerd
- **✗ Ontbreekt** — handboek beschrijft het, tooling heeft het (nog) niet

---

## 1. Volledig gedekte onderdelen

De onderstaande handboek-elementen zijn aantoonbaar gedekt in het datamodel. Geen actie vereist.

| Handboek-element | Paragraaf | Tooling-entiteit |
|---|---|---|
| Informatiebeveiliging (ISMS) | §1 | ISMS-domein, ISO27001/BIO frameworks |
| Privacybescherming (PIMS) | §1 | ProcessingActivity, DataSubjectRequest, ProcessorAgreement |
| Business Continuity (BCMS) | §1 | ContinuityPlan, ContinuityTest, BIAThreshold |
| BIO 2.0, ISO 27001, ISO 22301, ISO 27701, AVG | §2 | FrameworkType enum + Standard entiteit |
| Contextanalyse | §4.1 | OrganizationContext / OrganizationProfile (Hiaat 4) |
| Dreigingen (cyber, fysiek, organisatorisch) | §4.1 | Threat, ThreatActor, ThreatCategory (MAPGOOD) |
| Ketenafhankelijkheden / leveranciers | §4.1 | ScopeDependency, ProcessorAgreement, Stakeholder |
| Belanghebbenden | §4.2 | Stakeholder (migratie 017) |
| Toepassingsgebied / scope-hiërarchie | §4.3 | Scope (Hiaat 2): Org → Cluster → Afd → Proces → Asset |
| Verklaring van Toepasselijkheid | §4.4 | ApplicabilityStatement |
| Risicoregister | §4.4 / §8.2 | Risk, RiskScope (Hiaat 8) |
| Documentenregister | §4.4 | Policy, Attachment, Document |
| Three Lines of Defence | §5.2 / §5.4 | UserScopeRole: Eigenaar, Coordinator, Toezichthouder, … |
| Restrisico-acceptatie / besluitlog | §5.1 | Decision (type: Risk Acceptance) (Hiaat 1) |
| Directiebeoordeling (§9.3) | §5.5 / §9.3 | ManagementReview |
| DPIA's | §8.2 | Assessment type DPIA |
| Strategische + operationele risicoanalyse | §8.2 | Risk, Assessment, RiskFramework (Hiaat 3) |
| Risicobehandeling / maatregelen | §8.3 | Control, Measure, ControlRiskScopeLink |
| Doelstellingen & KPI's | §6.2 | Objective, ObjectiveKPI |
| Non-conformiteiten → correctieve acties | §10.1 | Finding → CorrectiveAction (Hiaat 7) |
| Continue verbetering | §10.2 | Initiative, BacklogItem |
| Risicobereidheid | §4.1 / §6 | RiskAppetite (6 niveaus, Hiaat 9) |
| Interne audit | §9.2 | Assessment type Audit |
| Incidentenregistratie | §4.4 | Incident + IncidentControlLink |
| Beleidsworkflow (Concept → Gepubliceerd) | §7.5 | Policy (PolicyState enum) |
| Jaarplanning audits / reviews | §6 | CompliancePlanningItem |
| In Control status per scope | §9.1 | InControlAssessment (Hiaat 5) |

---

## 2. Gedeeltelijk gedekte onderdelen (⚠️)

### 2.1 SWOT-analyse als gestructureerde entiteit

**Handboek (§4.1)**: De gemeente identificeert interne en externe issues via een SWOT-analyse. De uitkomsten worden gebruikt om het toepassingsgebied bij te stellen en risico's en kansen te bepalen.

**Situatie**: OrganizationProfile/OrganizationContext bestaat (Hiaat 4), maar bevat geen gestructureerde SWOT-velden (Strengths, Weaknesses, Opportunities, Threats) als aparte attributen of sub-entiteiten. SWOT-resultaten kunnen nu alleen als vrije tekst worden vastgelegd.

**Actieplan**:
1. Bekijk de huidige velden in `OrganizationProfile` / `OrganizationContext` in `core_models.py`.
2. Voeg een `SWOTAnalysis`-entiteit toe (of velden op OrganizationProfile) met vier categorieën: `strengths`, `weaknesses`, `opportunities`, `threats` (elk als tekstveld of JSON-array).
3. Koppel SWOT-items aan de risicobereidheid en aan contextgerelateerde risico's (`Risk`).
4. Voeg een migratie toe (volgnummer 018 of hoger).
5. Voeg een pagina-sectie toe in `Mijn Organisatie` (stap 1 van de onboarding wizard).
6. Update de `onboarding_agent` en `scope_agent` met context over SWOT.

**Prioriteit**: Middel — relevant voor directiebeoordeling en jaarlijkse herziening van het IMS.

---

### 2.2 Stakeholder-eisen gekoppeld aan beheersdoelstellingen

**Handboek (§4.2)**: Stakeholder-eisen worden geïdentificeerd en vertaald naar beheersdoelstellingen binnen het IMS. Ze worden periodiek geëvalueerd.

**Situatie**: `Stakeholder`-entiteit bestaat (migratie 017), maar een expliciete koppeling `Stakeholder → Requirement` of `Stakeholder → Objective` ontbreekt. De vertaalslag van stakeholder-eis naar beheersdoelstelling is niet traceeerbaar.

**Actieplan**:
1. Voeg een `StakeholderRequirement`-entiteit toe (of een koppeltabel `StakeholderObjectiveLink`) waarmee een stakeholder-eis aan een Objective of Requirement wordt gekoppeld.
2. Alternatief: voeg een `requirements`-veld (tekst of JSON) toe aan de bestaande Stakeholder-entiteit, plus een many-to-many naar `Objective`.
3. Voeg een migratie toe.
4. Toon de koppeling op de Leveranciers/Stakeholders-pagina.
5. Update de `planning_agent` en `objectives_agent`.

**Prioriteit**: Laag-middel — ISO 27001 vereist aantoonbare vertaling van stakeholder-context naar het systeem.

---

### 2.3 Rapportage-niveaus SIMS / TIMS / Directieteam als vaste targets

**Handboek (§5.5)**: De rapportagestructuur kent vier niveaus: operationeel → discipline-eigenaar → TIMS → SIMS → Directieteam, met vaste frequenties (tweewekelijks, maandelijks, kwartaal, 2x per jaar) en gespecificeerde inhoud per niveau.

**Situatie**: `ScheduledReport` en `ReportTemplate` bestaan, maar de vier rapportage-ontvangers (TIMS, SIMS, Directieteam) zijn niet als gestructureerde targets gemodelleerd. Rapporten zijn generiek — niet gekoppeld aan een specifiek overlegorgaan of niveau.

**Actieplan**:
1. Voeg een `report_level`-veld toe aan `ScheduledReport` (enum: Operationeel, Discipline, TIMS, SIMS, Directieteam).
2. Indien SIMS/TIMS als entiteiten worden toegevoegd (zie §3.1): koppel `ScheduledReport` aan het ontvangende orgaan.
3. Definieer per rapportage-niveau een default `ReportTemplate` met de vereiste inhoud uit het handboek (§5.5).
4. Voeg filtering op rapportage-niveau toe aan het Rapportage-dashboard.

**Prioriteit**: Middel — wordt urgent zodra SIMS/TIMS als entiteiten worden geïmplementeerd.

---

### 2.4 Cyberbeveiligingswet / NIS2 als FrameworkType

**Handboek (§2)**: De Cyberbeveiligingswet en NIS2-richtlijn zijn normatieve verwijzingen waaraan de gemeente moet voldoen.

**Situatie**: De `FrameworkType`-enum bevat: BIO, ISO27001, AVG, BCM, NEN7510, Other. NIS2 en Cyberbeveiligingswet zijn niet als aparte types opgenomen. Ze vallen nu onder `Other`, wat traceerbaarheid en rapportage bemoeilijkt.

**Actieplan**:
1. Voeg `NIS2` en `Cyberbeveiligingswet` toe aan de `FrameworkType`-enum in `core_models.py`.
2. Maak een Alembic-migratie die de enum uitbreidt (gebruik raw SQL, conform bestaand patroon voor enum-uitbreiding).
3. Voeg de bijbehorende `Standard`-records toe als seed-data in het initialisatiescript.
4. Koppel relevante NIS2-vereisten als `Requirement`-records (kunnen initieel beperkt zijn).
5. Update de `compliance_agent` zodat hij NIS2-vragen herkent.

**Prioriteit**: Hoog — wettelijke verplichting voor gemeenten; ontbreekt nu als eigen framework.

---

### 2.5 Overige wetgeving als Standards (Wpg, Wjsg, Woo, Archiefwet, Wbni)

**Handboek (§4.1)**: De gemeente heeft te maken met de Wpg, Wjsg, Woo, Archiefwet 1995 en Wbni.

**Situatie**: Geen van deze wetten is als aparte `Standard`-record ingericht. Ze vallen onder `Other` of worden niet bijgehouden.

**Actieplan**:
1. Voeg de volgende records toe als `Standard` (FrameworkType: Other of een nieuw type `Wetgeving`):
   - Wet politiegegevens (Wpg)
   - Wet justitiële en strafvorderlijke gegevens (Wjsg)
   - Wet open overheid (Woo)
   - Archiefwet 1995
   - Wet beveiliging netwerk- en informatiesystemen (Wbni)
2. Voeg minimale `Requirement`-records toe voor de kernverplichtingen per wet.
3. Koppel via de Rosetta Stone (`RequirementMapping`) waar overlapping bestaat met BIO/ISO.
4. Overweeg een FrameworkType `Wetgeving` naast de ISO-types.

**Prioriteit**: Laag — relevant voor volledigheid van het compliance-beeld, maar niet blokkerend.

---

### 2.6 Budget- en middelenregistratie

**Handboek (§5.1 / §7.1)**: Het directieteam is verantwoordelijk voor het beschikbaar stellen van voldoende financiële middelen en tooling. Het TIMS kan aanvullende middelen aanvragen.

**Situatie**: Er is geen entiteit voor budget, middelentoewijzing of capaciteitsregistratie in het datamodel.

**Actieplan**:
1. Overweeg een `ResourceAllocation`-entiteit gekoppeld aan `Objective` of `Initiative` (budget, FTE, tooling).
2. Minimale variant: voeg een `budget_allocated` en `budget_spent` veld toe aan `Initiative`.
3. Toon budgetindicator op het Initiative-overzicht en in de directiebeoordeling (ManagementReview).
4. Beslis eerst of dit in scope is van de tooling of eerder thuishoort in een P&C-tool.

**Prioriteit**: Laag — hangt af van de gewenste scope van de tooling vs. externe financiële systemen.

---

## 3. Ontbrekende onderdelen (✗)

### 3.1 SIMS en TIMS als formele entiteiten

**Handboek (§5.3 / Bijlage 1)**: Het IMS kent drie overlegstructuren:
- **SIMS** (Strategisch IMS-team): kwartaal, samenstelling: Directeur IDA, Directeur [x], Concerncontroller, CISO + roulerend TIMS-lid
- **TIMS** (Tactisch IMS-team): maandelijks, samenstelling: CIO, CISO, Concerncontroller, CARM, BCM'er, FG, Manager IB&P, Interne accountant
- **Discipline-eigenaren** (Operationeel): per domein (BCM → BCM'er, IB/Privacy → Manager IB&P)

Deze organen zijn ook de escalatieniveaus in Bijlage 1.

**Situatie**: Volledig afwezig in het datamodel. Users en rollen bestaan, maar er is geen `GovernanceBody`-concept.

**Actieplan**:
1. Ontwerp een `GovernanceBody`-entiteit met velden: `name`, `type` (enum: SIMS / TIMS / DisciplineOwner / Other), `meeting_frequency` (enum: Weekly / Biweekly / Monthly / Quarterly / Biannually), `mandate`, `tenant_id`.
2. Voeg een `GovernanceBodyMember`-koppeltabel toe: `governance_body_id`, `user_id`, `role_in_body` (Voorzitter, Lid, Secretaris, Roulerend lid), `start_date`, `end_date`.
3. Voeg een `GovernanceMeeting`-entiteit toe voor vergaderregistratie: `date`, `agenda`, `minutes`, `decisions_made` (koppeling naar Decision), `governance_body_id`.
4. Koppel de escalatieprocedure (Bijlage 1) door `Finding` en `Decision` te voorzien van een `escalated_to_id` (→ GovernanceBody).
5. Koppel `ScheduledReport` aan `GovernanceBody` als ontvanger (zie §2.3).
6. Voeg een Alembic-migratie toe.
7. Voeg een beheerpagina toe onder INRICHTEN voor het aanmaken en beheren van overlegorganen.
8. Update de `planning_agent` met kennis over SIMS/TIMS-cycli.

**Prioriteit**: Hoog — structurele basis voor escalatie, rapportage en bestuurlijke verantwoording zoals beschreven in het handboek.

---

### 3.2 Opleidingsregister en competentieregister

**Handboek (§7.2)**: De organisatie zorgt voor competentie via duidelijke rolbeschrijvingen, duidelijke rollen en verantwoordelijkheden, en adequate opleiding (met specifieke opleidingseisen per rol — nu nog placeholder `????`).

**Situatie**: Rolbeschrijvingen bestaan als `UserScopeRole`-toewijzingen, maar er is geen registratie van trainingen, certificaten of competenties per medewerker.

**Actieplan**:
1. Voeg een `Training`-entiteit toe: `title`, `type` (enum: Awareness / Opleiding / Certificering / Oefening), `provider`, `date_completed`, `valid_until`, `user_id`, `tenant_id`.
2. Voeg een `RequiredTraining`-entiteit toe of een koppeltabel `RoleTrainingRequirement`: welke trainingen zijn vereist voor welke `UserScopeRole`-rollen.
3. Voeg automatische meldingen (`Notification`) toe bij naderende verloopdatum van een certificering.
4. Toon een complianceoverzicht per medewerker/rol op de Gebruikers-pagina.
5. Update de `admin_agent` met context over opleidingsvereisten.

**Prioriteit**: Middel — ISO 27001 §7.2 en BIO 2.0 vereisen aantoonbare competentiebeheer.

---

### 3.3 Bewustzijnsprogramma (Awareness)

**Handboek (§7.3)**: Een deel van de opleiding voor iedereen die met informatie werkt omvat bewustzijn en begrip van het informatiebeveiligings- en privacybeleid, de verwachtingen en de consequenties van niet-naleving.

**Situatie**: `Notification` bestaat voor ad hoc berichten, maar er is geen gestructureerd bewustzijnsprogramma met campagnes, doelgroepen, leesbevestigingen of effectiviteitsmetingen.

**Actieplan**:
1. Voeg een `AwarenessCampaign`-entiteit toe: `title`, `topic` (enum: Informatiebeveiliging / Privacy / BCM / Algemeen), `target_group`, `start_date`, `end_date`, `status`, `content_url`, `tenant_id`.
2. Voeg een `AwarenessReadReceipt`-koppeltabel toe: `campaign_id`, `user_id`, `confirmed_at` — om aantoonbaar te maken wie het beleid heeft gelezen.
3. Koppel campagnes aan `Policy`-publicaties: bij publicatie van een nieuw beleidsdocument automatisch een campagne aanmaken.
4. Voeg een complianceoverzicht toe: hoeveel % van de medewerkers heeft de campagne bevestigd.
5. Toon openstaande campagnes op het persoonlijke Dashboard.
6. Update de `policy_agent` met context over bewustzijnsverplichtingen.

**Prioriteit**: Middel — BIO 2.0 en ISO 27001 §7.3 vereisen aantoonbaar bewustzijn; ook relevant bij audits.

---

### 3.4 Discipline-eigenaar als formele domeinrol

**Handboek (§5.3)**: Discipline-eigenaren zijn integraal verantwoordelijk voor de PDCA-cyclus binnen hun domein. De toewijzing is expliciet:
- Business Continuity → BCM'er
- Informatiebeveiliging → Manager IB&P
- Privacy → Manager IB&P

**Situatie**: `UserScopeRole` kent de rol `Eigenaar`, maar er is geen domein-georiënteerde eigenaarschapsregistratie. Een "discipline" (ISMS, PIMS, BCMS) is geen entiteit; je kunt niet formeel vastleggen wie de discipline-eigenaar is per domein.

**Actieplan**:
1. Voeg een `DisciplineOwner`-entiteit of koppeltabel toe: `domain` (enum: ISMS / PIMS / BCMS), `user_id`, `start_date`, `end_date`, `tenant_id`.
2. Gebruik dit in rapportages: rapportages per discipline worden automatisch gericht aan de verantwoordelijke discipline-eigenaar.
3. Koppel aan `GovernanceBody` (TIMS-samenstelling) via de bestaande of nieuwe lid-relatie.
4. Toon discipline-eigenaarschap zichtbaar op de organisatiepagina (`Mijn Organisatie`).
5. Voeg een Alembic-migratie toe.

**Prioriteit**: Middel — ondersteunt de escalatieprocedure en maakt verantwoordelijkheidsstructuur aantoonbaar.

---

## 4. Wat de tooling méér heeft dan het handboek beschrijft

Dit zijn functies in de tooling die het handboek nog niet noemt. Overweeg deze terug te laten komen in het handboek (toekomstige versie).

| Tooling-feature | Beschrijving | Relevantie voor handboek |
|---|---|---|
| **Multi-tenancy** | SSC → gemeente netwerk, shared controls | Relevant als Leiden diensten levert aan regiogemeenten |
| **MAPGOOD dreigingscatalogus** | Gestructureerde dreigingscategorieën | Concretiseert §4.1 "Dreigingen en ontwikkelingen" |
| **In Control kwadrant** | Mitigeren / Zekerheid / Monitoren / Accepteren | Operationaliseert de risicobereidheid uit §6 |
| **Rosetta Stone** | Cross-framework mapping (BIO ↔ ISO ↔ AVG) | Maakt de normatieve verwijzingen uit §2 aantoonbaar gerelateerd |
| **Monte Carlo simulatie** | Financiële kwantificering van risico's | Gaat verder dan het handboek nu beschrijft |
| **19 AI-agenten** | Domein-specifieke LLM-ondersteuning | Niet in handboek; ondersteunt alle PDCA-fasen |
| **TopDesk / ServiceNow integratie** | Incidenten ↔ correctieve acties | Operationaliseert §10.1 (non-conformiteiten) |
| **BacklogItem** | Verbeterideeën en feature requests | Past in §10.2 (continue verbetering) |

**Aanbeveling**: Voeg in een volgende versie van het handboek (§4.4 of een nieuw §11) een verwijzing toe naar de tooling-ondersteunde functies, zodat gebruikers weten hoe het handboek en de tooling samenhangen.

---

## 5. Openstaande placeholders in het handboek

De volgende onderdelen in het handboek zijn nog niet uitgewerkt en vereisen inhoudelijke input (geen tooling-actie):

| Paragraaf | Placeholder | Actie (buiten tooling) |
|---|---|---|
| §4.1 | `<tekst> van Luuk – eerste concept` | Contextanalyse uitschrijven |
| §4.1 | Visie: `<OMSCHRIJVING>` | Invullen via bestuurlijk proces |
| §4.1 | Missie: `<OMSCHRIJVING>` | Invullen via bestuurlijk proces |
| §4.1 | Strategie: `<OMSCHRIJVING>` | Invullen via bestuurlijk proces |
| §7.2 | Opleidingseisen: `????` | Invullen per rol (CISO, BCM'er, FG, etc.) |
| §7.2 | Specifieke opleidingsinhoud: `o  ????` | Uitwerken bewustzijnsmatrix per functie |
| §9.2 | Interne audit: `Tekst tekst, willen we dit?` | Beslissing nemen over inrichting interne audit |
| §2 | Overige normen: `document x` | Invullen of koppelen aan document in tooling |

---

## 6. Prioriteringsoverzicht

| # | Item | Type | Prioriteit | Tooling-actie? |
|---|---|---|---|---|
| 1 | SIMS/TIMS als formele entiteiten | ✗ Ontbreekt | **Hoog** | Ja — GovernanceBody + Meeting |
| 2 | Cyberbeveiligingswet / NIS2 als FrameworkType | ⚠️ Gedeeltelijk | **Hoog** | Ja — enum uitbreiden |
| 3 | Opleidingsregister / competentieregister | ✗ Ontbreekt | **Middel** | Ja — Training-entiteit |
| 4 | Bewustzijnsprogramma (awareness) | ✗ Ontbreekt | **Middel** | Ja — AwarenessCampaign-entiteit |
| 5 | Discipline-eigenaar als formele domeinrol | ✗ Ontbreekt | **Middel** | Ja — DisciplineOwner-entiteit |
| 6 | SWOT als gestructureerde entiteit | ⚠️ Gedeeltelijk | **Middel** | Ja — velden op OrganizationProfile |
| 7 | Rapportage-niveaus als vaste targets | ⚠️ Gedeeltelijk | **Middel** | Ja — report_level op ScheduledReport |
| 8 | Stakeholder-eisen → beheersdoelstellingen | ⚠️ Gedeeltelijk | **Laag-middel** | Ja — StakeholderObjectiveLink |
| 9 | Overige wetgeving als Standards | ⚠️ Gedeeltelijk | **Laag** | Ja — seed-data toevoegen |
| 10 | Budget- en middelenregistratie | ⚠️ Gedeeltelijk | **Laag** | Optioneel — afhankelijk van scope |
| 11 | Handboek aanvullen met tooling-features | — | **Laag** | Nee — handboek-actie |
| 12 | Placeholders handboek invullen | — | **Hoog** | Nee — inhoudelijke actie buiten tooling |

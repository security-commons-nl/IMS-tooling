# Kritische analyse — IMS-proces ontwerp

*Benchmarked against: ServiceNow GRC, Vanta, Drata, LogicGate, ARCHER, ISO 27001 certification bodies*
*Gegenereerd: 2026-03-18*

---

## Prioriteringsoverzicht

| # | Bevinding | Ernst | Actie |
|---|-----------|-------|-------|
| 4 | Normversioning ontbreekt | Hoog | Backlog — architectuurkeuze nu vastleggen |
| 2 | 18 agents → onderhoudslast | Hoog | Heroverweeg agent-architectuur bij bouw |
| 6 | PDF-parsing fragiel | Hoog | Primaire invoer = formulieren, PDF = optioneel |
| 7 | IP in besluitlog | Hoog | Verwijderen, AVG-risico |
| 3 | Document vs. data spanning | Medium | Expliciet vastleggen: DB is altijd leidend |
| 5 | Visibility edge cases | Medium | Drie scenario's uitwerken voor datamodel |
| 8 | Volwassenheidsprofiel regressie | Medium | Score koppelen aan data, niet aan stap-historie |
| 10 | Fase-overgangscriteriaontbreken | Medium | Per fase-overgang exit criteria definiëren |
| 9 | "Simpel" niet geoperationaliseerd | Laag | Drie UI-principes vastleggen |
| 1 | 22 stappen cognitieve last | Laag | "Waarom nu"-veld toevoegen per stap |

---

## 1. Het 22-stappenproces — cognitieve last

**Bevinding: solide, maar cognitieve last is een risico.**

Vanta en Drata doen onboarding in <10 stappen — maar die platforms richten zich op snelle SaaS-certificering voor tech-bedrijven, niet op gemeenten met drie domeinen (ISMS/PIMS/BCMS) en democratische governance. Vergelijkbare GRC-implementaties bij overheid (ServiceNow GRC, ARCHER) lopen 6-18 maanden en hebben vergelijkbare stap-aantallen.

**Wat werkt:** De fasering (Fase 0-3) is een bewuste keuze om niet alles tegelijk te eisen. Dat is industrie-standaard: *progressive complexity*.

**Risico:** Stappen zijn genummerd 1-22, maar de gebruiker ziet niet wat er achter stap 10 zit als ze op stap 3 zitten. Dat vergroot afhankelijkheid van de implementatiecoördinator.

**Aanbeveling:** Voeg per stap een *"waarom nu"*-veld toe in het stap-patroon (naast input/output/agents). Maakt de methodologie zelfdragend.

---

## 2. 18 AI agents — onderhoudslast

**Bevinding: architectureel risico — zwaarste knelpunt.**

Industry norm: platforms zoals LangChain en AutoGEN convergeren naar **minder, meer generieke agents** met gespecialiseerde tools. Elke agent heeft een eigen system prompt, eigen tool-set, eigen foutgedrag — en dat schalt slecht.

**Probleem:** Als BIO 2.0 wijzigt, moeten mogelijk 8-10 agents worden bijgewerkt die BIO-kennis in hun prompt dragen.

**Risico's:**
- 18 agents × 3 domeinen = potentieel 54 combinaties die getest moeten worden
- Geen mechanisme voor *agent-versioning* — hoe wordt een slechte output teruggedraaid?
- Prompt injection: door-de-gebruiker-ingevoerde documenten kunnen agents aansturen

**Aanbeveling:** Reduceer tot 6-8 *domain agents* (ISMS, PIMS, BCMS, Governance, Risk, Compliance, Reporting, Admin) + 1 orchestrator. Domein-agents krijgen tools, geen embedded kennis. Kennis zit in een RAG-store die los van de agents wordt bijgehouden. Dit is het **LangGraph/CrewAI-patroon** dat nu industrie-standaard is.

---

## 3. Document-centric vs. data-centric

**Bevinding: juiste keuze voor de doelgroep, maar spanning met de GRC-engine.**

De trend in GRC (Vanta, Secureframe, Tugboat Logic) is **data-centric**: geen documenten, maar gestructureerde data met een weergave-laag. IMS-proces kiest bewust voor document-output — correct voor gemeenten, want auditoren, gemeenteraad en juristen verwachten documenten.

**Risico:** Als het handboek als document wordt gegenereerd en daarna de scope wijzigt in de GRC-tool — zijn ze dan nog gesynchroniseerd? Dit is het *two source of truth*-probleem dat expliciet vermeden moet worden.

**Aanbeveling:** Documenten zijn **gegenereerde views** van structurele data, nooit de bron zelf. De database is altijd leidend. Het handboek is een rapport, geen bestand. Dit moet expliciet worden vastgelegd in de architectuurbeslissingen.

---

## 4. Normversioning — blinde vlek

**Bevinding: niet ontworpen, maar zeker een probleem.**

BIO 2.0 → BIO 3.0 gaat komen. ISO 27001:2022 was zelf een grote revisie van 2013. Wat gebeurt er met:
- RequirementMappings die verwijzen naar controls die zijn hernummerd of vervallen?
- SoA-scores die zijn gebaseerd op de oude norm?
- Auditresultaten die refereren aan de vorige versie?

**Industry-aanpak (ServiceNow GRC):** Elke norm heeft een `version_id`. Mappings zijn `norm_version`-gebonden. Bij een normupdate wordt een migratiewizard aangeboden die bestaande mappings probeert te hergebruiken en vlaggen wat handmatig review nodig heeft.

**Aanbeveling:** Voeg `norm_version` toe aan Standard/Requirement-entiteiten. Zorg dat RequirementMapping verwijst naar specifieke versie, niet naar de norm in het algemeen.

---

## 5. Visibility-layer — edge cases

**Bevinding: het model klopt, maar drie edge cases zijn niet afgedekt.**

**a) Visibility-downgrade:** Leiden zet normenkader op `regionaal`. Leiderdorp leest het. Leiden zet het terug op `privé`. Wat ziet Leiderdorp?
→ *Aanbeveling:* Bij downgrade: tombstone ("dit document is niet meer beschikbaar") + datum terugtrekking. Nooit stille verwijdering.

**b) Conflicterende normen:** Leiden en Leiderdorp publiceren allebei een normenkader als `regionaal`. Welke is leidend?
→ *Aanbeveling:* Eén gemeente per regio is norm-eigenaar (aangewezen in regio-configuratie). Anderen kunnen lezen, niet overschrijven.

**c) Audit trail:** Als een regionale toezichthouder regionaal-zichtbare compliance-scores bekijkt, wordt dat gelogd?
→ *Aanbeveling:* Ja, verplicht. AVG art. 30 + accountability-principe.

---

## 6. PDF-parsing als input — fragiel

**Bevinding: grootste technische fragiliteitspunt.**

De gap-analyse agent leest bestaande beleidsdocumenten (PDF) en vergelijkt die met normeisen. PDF-parsing is notoir onbetrouwbaar: tabellen worden platte tekst, headers raken hun structuur kwijt, gescande PDFs zijn onleesbaar.

**Industry-aanpak:** Vanta vraagt gebruikers om gestructureerde input via formulieren. Drata koppelt aan API's. Niemand vertrouwt op PDF-parsing als enige invoerroute.

**Aanbeveling:** PDF als *optionele* invoer, niet als primaire route. Primaire route: gestructureerde vragenlijsten in de wizard die directe database-invoer opleveren. PDF-parsing als *aanvullende context* voor de agent, met expliciete onzekerheidsmarkering in de output ("gebaseerd op PDF-extractie — verifieer handmatig").

---

## 7. Besluitlog — juridische houdbaarheid

**Bevinding: goed idee, maar IP-adres is een AVG-risico.**

**Probleem 1:** IP-adressen zijn persoonsgegevens onder AVG. Ze opslaan vereist een grondslag en een retentieperiode — die nog niet zijn gedefinieerd. Veel gemeenten werken met shared IP's (NAT, VPN), wat IP-adressen ook weinig zeggen over wie de beslissing nam.

**Probleem 2:** Voor risicobesluiten boven een bepaalde drempel is in sommige gemeenten een formele procuratieregeling van kracht. Dan is `naam + functie` niet voldoende — er is een formele mandatering nodig.

**Industry-aanpak:** ARCHER en ServiceNow GRC gebruiken *digitale handtekening* (PKI of eHerkenning) voor formele risicobesluiten, en slaan geen IP op.

**Aanbeveling:** IP-adres verwijderen of achter een feature flag. Vervang door `session_id` (intern, niet herleidbaar) of laat volledig weg. Voor hoge-drempel besluiten: onderzoek eHerkenning-integratie (backlog).

---

## 8. Volwassenheidsprofiel — regressie niet ontworpen

**Bevinding: het model groeit, maar krimpt niet.**

Het volwassenheidsprofiel groeit door stap 4/5/7/8/9. Maar: wat als een gemeente een stap terugzet of een auditor concludeert dat stap 7 herhaald moet worden?

**Industry-aanpak (CMMI, Gartner Maturity Models):** Volwassenheidsscores zijn point-in-time metingen, niet permanente state. Ze worden periodiek herberekend op basis van actuele data.

**Aanbeveling:** Koppel de volwassenheidsscore aan de actuele toestand van de GRC-data, niet aan de stap-doorloophistorie. Stap-doorloop is een *trigger* voor herberekening, niet de score zelf.

---

## 9. "Simpel voor de gebruiker" — niet geoperationaliseerd

**Bevinding: principe staat er, uitwerking ontbreekt.**

22 stappen + 18 agents + multi-tenant RBAC + twee modi + cyclus_id + blokkade-principe = inherente complexiteit die verborgen moet worden, niet vereenvoudigd.

**Industry-aanpak (Notion, Linear, Vanta):** Progressive disclosure. Een gebruiker ziet alleen wat relevant is voor zijn rol en huidige stap.

**Drie concrete UI-principes:**
1. **Role-aware UI**: elke view filtert op `user.role + user.scope` — nooit een "alles-scherm"
2. **Step-aware UI**: actieve stap staat centraal, toekomstige stappen zijn dimmed/vergrendeld
3. **Complexity ceiling**: als een wizard meer dan 5 vragen heeft → opsplitsen of betere volgorde kiezen

---

## 10. Fase-overgangscriteriaontbreken

**Bevinding: de 4 fasen zijn beschreven, maar de overgangscriteria niet.**

Wanneer gaat een gemeente van Fase 0 naar Fase 1? "Als het IMS is ingericht" is te vaag. ServiceNow GRC en ARCHER gebruiken *exit criteria*: een gedefinieerde checklist die door een gremium wordt geaccordeerd.

**Aanbeveling:** Definieer per fase-overgang minimaal:
- Welke stappen moeten zijn afgerond (status = vastgesteld)?
- Welk gremium accordeert (SIMS, TIMS, of extern)?
- Wat is de documentaire neerslag (besluitlog-entry met type "fase-overgang")?

---

## Wat er goed zit

De volgende elementen zijn solide en industrie-conform:
- Twee-modi-architectuur (inrichtings- + beheermodus)
- Blokkade-principe (B/W/V-scheiding)
- Multi-tenant visibility-laag (concept)
- Rosetta Stone voor normenmapping (RequirementMapping)
- Fasering 0→3 (progressive complexity)
- Twee-agent pattern (gap-analyse breed + domein-agent stap-specifiek)

De gevonden risico's zijn bouwbaar — geen fundamentele fouten, wel gaten die nu goedkoper zijn op te lossen dan later.

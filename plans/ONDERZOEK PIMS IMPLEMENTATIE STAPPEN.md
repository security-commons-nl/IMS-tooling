# Executive Summary

Een **Privacy Information Management System (PIMS)** is een bestuurlijk gestuurd, risico-gebaseerd raamwerk om te voldoen aan de AVG/GDPR. In essentie is een PIMS een uitbreiding op het ISMS (ISO 27001) met focus op privacy: het helpt organisaties aantoonbaar passende technische en organisatorische maatregelen te nemen, zoals vereist in **GDPR artikel 32** (risicogebaseerde beveiliging) en **artikel 35** (DPIA bij hoge risico’s). ISO/IEC 27701 biedt een internationaal erkende norm (met dezelfde structuur als ISO 27001) voor het opzetten en onderhouden van zo’n PIMS【22†L2955-L2963】【14†L2318-L2326】. 

De stappen zijn circulair (PDCA) en omvatten: 1) **Initiatie & scope** (bestuurlijke afbakening, risicoacceptatie, compliance mapping), 2) **Risicoanalyse & plannen** (datamapping, DPIA-screening, selectie privacy-maatregelen), 3) **Implementatie maatregelen** (privacybeleid, DPIA-proces, verwerkerscontracten, meldprocessen, awareness), 4) **Monitoring & controle** (audits, rapportages, managementreview, continue toetsing van DPIA’s/datalekken) en 5) **Verbeteren & certificeren** (correcties, herhaalde risico-evaluatie, optioneel ISO 27701-certificering). Per stap zijn er concrete deliverables (bijv. PIMS-beleidsdocument, verwerkingsregister, DPIA-rapporten, registraties van datalekken), met bijbehorende rollen (DPO/FG, privacy officer, IT-security, jurist, inkoop), tools (GRC-systeem, DPIA-tool, IAM/MFA, SIEM, ITSM) en meetbare criteria (bijv. % afgesloten DPIA’s, auditbevindingen, meldtijd datalekken). Tabeloverzichten voor deliverables/templates en succescriteria verduidelijken dit structuur.

ISO 27701 en de GDPR vullen elkaar aan: ISO 27701 wijst op “geautoriseerde codes of conduct of certificeringen” als bewijsmiddel【14†L2356-L2363】, terwijl de GDPR harde verplichtingen stelt (o.a. DPIA, brechtmelding binnen 72 uur). ISO 27701 is daarom geen vervanging maar een **hulpmiddel** om GDPR-naleving gestructureerd in te richten. De Autoriteit Persoonsgegevens erkent het belang van ISO 27701 voor AVG-naleving【3†L49-L52】. Nederlands/europese regelgeving (GDPR zelf, Nederlandse UAVG-regels, NIS2 voor veiligheid) wijst op vergelijkbare risicogebaseerde eisen (zie ISO-27701 annex), en EDPB-richtlijnen (bijv. DPIA en breach handling) bieden operationele duiding. Europese bronnen (EUR-Lex, ENISA) bevestigen dat ISO 27701 een “extension” is voor privacybeheer【22†L2955-L2963】【26†L280-L287】 en dat dit aansluit op geautomatiseerde rapportage (SIEM) en governance. 

Praktijkcases (bijv. gemeenten met ISO 27001/27701-certificering, of grote organisaties die breder datalekbeheer inregelen) laten zien dat een goed ingericht PIMS de AVG-compliance verhoogt en inkoopvoorwaarden afdwingt. Elk organisatiegrootte heeft eigen nuances: klein kan starten met een beperkte scope en sjablonen, groot moet rekening houden met gedistribueerde data-eigenaren en professionele tooling. Hieronder volgt een gedetailleerd stappenplan, inclusief procesflows, tabellen en een implementatieroadmap voor klein/middel/groot, gericht op **evidence-based continious improvement** in lijn met PDCA en wet- en regelgeving.

## Normatieve en wettelijke context

### GDPR/AVG en nationaal kader

De **AVG/GDPR** legt de kerneisen vast voor privacybeheer:
- **Artikel 5**: (rechtmatigheid, doelbinding, dataminimalisatie, bewaartermijn) vereist gedocumenteerde verwerkingsprincipes.  
- **Artikel 25 (Privacy by Design/Default)**: verplicht dat in de ontwerpfase van elk verwerkingstraject privacymaatregelen zijn ingebouwd. ISO 27701 ondersteunt dit via verplichte documentatie (PDIA’s, DPIA’s in SoA).  
- **Artikel 32**: vereist passende technische/organisatorische maatregelen op basis van risico【14†L2318-L2326】 (zoals encryptie, systeemresilience, herstelplan, continue toetsing). Dit is de basis voor controleselectie in een PIMS.  
- **Artikel 33-34**: verplicht meldingen van datalekken binnen 72 uur, plus documentatie daarvan (huishouding register). PIMS dient processen en ICT-systemen te bevatten om incidenten centraal te registreren en te volgen.  
- **Artikel 35**: verplicht een Data Protection Impact Assessment (DPIA) bij hoog-risicoverwerkingen. Een PIMS-beheerproces moet in staat zijn de noodzaak van DPIA’s te identificeren, uit te voeren en bij te houden (tools voor DPIA-registratie).  
- **Artikel 39**: benoemt de (taak van de) functionaris gegevensbescherming (FG/DPO) die toezicht houdt op compliance en fungeert als privacyexpert. In het PIMS-team is een FG/DPO veelal projectleider of toezichthouder.  

Op nationaal niveau is de **Uitvoeringswet AVG (UAVG)** relevant. Voor gemeenten: u.a. plicht FG (art. 53 Wpb) en nationale boetelijst voor overtredingen. De **Autoriteit Persoonsgegevens (AP)** publiceert handreikingen (bijv. verwerkersovereenkomsten, DPIA, gegevensuitwisseling) en benadrukt het belang van systematische gegevensbescherming. De AP adviseert ISO 27701 zelfs voor certificering om AVG-naleving te borgen【3†L49-L52】. 

### Internationale standaarden en aanbevelingen

**ISO/IEC 27701 (2021)** is een uitbreiding (“privacy extension”) op ISO 27001/27002【22†L2955-L2963】, met **extracontroles voor privacy** (zoals verwerkingsovereenkomsten, transparantie, minimisatie) en guidelines voor privacymaatregelen. Het is als zodanig een ** internationaal erkende best-practice**: ENISA noemt expliciet dat ISO 27701 PIMS-richtlijnen specificeert【22†L2955-L2963】. 

ISO 27701 is **niet bindend**, maar biedt een raamwerk dat exact aansluit op GDPR-eisen. Zo stelt artikel 32 lid 3 GDPR dat naleving van “erkende gedragscodes of certificatie” kan helpen aan te tonen dat aan veiligheidsvereisten is voldaan【14†L2356-L2363】. ISO 27701 kan een zodanig certificatiemiddel zijn. De NEN vertaalt dit in Nederland als NEN-EN-ISO/IEC 27701:2021 (vormgeeft eisen voor PIMS)【22†L2955-L2963】. 

Naast ISO-standaarden publiceert het Europese **ENISA** rapporten en guidance: o.a. een overzicht van risicomanagementstandaarden met vermelding van ISO 27701 als framework voor een PIMS【22†L2955-L2963】. ENISA heeft ook casussen en voorbeeld-evidenties voor privacymaatregelen (denk aan DPIA-protocol, incident response, ketenbeveiliging) die gebruikt kunnen worden in een PIMS-implementatie. 

### Aanvullende wet- en regelgeving

- **NIS2/Cybersecuritywet**: hoewel primair cyber- en netwerkbescherming, snijdt NIS2 raakvlak met privacy (bestuurlijke beveiligingseisen, incidentrapportage, ketenbeveiliging). Een PIMS draagt bij aan NIS2 compliance door bijvoorbeeld data-integriteit en systeemherstel te regelen. (Het kabinet heeft aangekondigd NIS2 ook op gemeenten toe te passen【4†L2-L8】.)  
- **DORA**: regelgeving voor financiële sector; voor gemeenten relevant als ze financiële diensten verzorgen (bv. woonlastendienstverlening). DORA vereist strikte ICT-risicomanagement en governance, vergelijkbaar met GDPR-beveiliging, dus PIMS-maatregelen kunnen ook DORA-risico’s dekken.  
- **AP-richtlijnen en handreikingen**: de AP (als nationale toezichthouder) geeft regelmatig aanvullende uitleg, bijvoorbeeld over verwerkingsregisters, DPIA, FOIA/AVG-verzoeken, etc. Deze vormen praktische invulling van PIMS-processen.  

De kern is dat **ISO 27701 en GDPR elkaar versterken**: 27701 specificeert *hoe* je governance en controles structureel organiseert, terwijl de wet de *waarborgen* stelt (zoals 32, 33, 35). Organisaties kunnen via ISO 27701 aantonen aan de AP (of tijdens audits) dat aan het wettelijk kader voldaan is, mits alle relevante regels zijn gemapt.

## ISO/IEC 27701 versus GDPR-benadering

- **Certificering vs. wetgeving**: ISO 27701 is een *standaard*, géén wet. Voldoen aan ISO 27701 betekent niet automatisch wettelijke naleving, maar de norm is opgezet om GDPR-vereisten te adresseren. AP erkent dit kader (advies tot verplichtstelling【3†L49-L52】) omdat het organisaties “dwingt” documentatie, beleid en processen in te richten die de AVG uitdiepen. Daarbij vult de norm (zelfregulering) de wet aan: normen helpen je aantonen dat je aan de regels voldoet【4†L33-L41】. Echter: een organisatie kan ISO-gestuurd zijn, maar als zij een privacyprincipe uit de GDPR overslaat (bijv. grondslag of dataminimalisatie) blijft er een nalevingsrisico.

- **Structuur en focus**: De GDPR volgt een juridisch-juridisiche benadering (verwerkingsprincipes, rechten van betrokkenen, plichten voor verwerkers/controller). ISO 27701 is van oorsprong een **managementsysteem**benadering: het schrijft een *proces* voor (PDCA) en *controls*, niet juridische definities. 27701 beschrijft *wat* ingericht moet zijn (bijv. verwerkersovereenkomst, DPIA-proces, gegevensbeheerbeleid), terwijl de GDPR *waarom* en *wat* (doelbinding, rechtmatigheid, transparantie) voorschrijft. 

- **Risk-based aanpak**: Beide systemen benadrukken risicomanagement. De GDPR vereist maatregelen “passend bij het risico”【14†L2318-L2326】, ISO 27701 beschrijft controles onderverdeeld per risico-/controlobject (bv. “PII controllers”, “consent”, “datasubjectrechten”). In de praktijk betekent dit: het PIMS-programma voert een risicocontrolecyclus in (impactanalyses, risico-eigenaars) die zowel GDPR-risico’s als informatiebeveiligingsrisico’s omvat.

- **Beheer van persoonsgegevens**: ISO 27701 voegt Annex A/B-controles toe die specifiek zijn voor privacy (bv. recht van inzage, wilsverklaringen, DPIA’s, verwerkerbeheer). Dit vult de AVG-normen aan: GDPR-artikelen als 13-15 (informatie aan betrokkenen, inzagerecht), 22 (profilering), 28 (verwerkersplicht) krijgen in ISO-termen procesbeschrijvingen en documentatie-eisen. 

- **Onderlinge afhankelijkheid**: Een ISMS (ISO 27001) legt een basisbeveiliging, PIMS breidt dat uit naar privacy. Zoals BMGrip stelt: “Een PIMS is een uitbreiding van het ISMS... Een PIMS is daarom uitermate geschikt om te combineren met ISO 27001”【26†L278-L287】. In technische zin betekent dit dat veel beveiligingsmaatregelen (toegangsbeheer, logging, encryptie) dubbel tellen voor beide; maar PIMS voegt extra processen toe, zoals DPIA, verwerkers-checks, sensitieve data-analyse. 

Kortom, ISO 27701 biedt structuur en bewijsvoering voor een compliant privacybeleid, terwijl de GDPR het wettelijk mandaat blijft. In het stappenplan hieronder wordt deze combinatie vanzelf duidelijk: GDPR-vereisten sturen de doelen (bv. “bewaartermijn vastleggen”, “melding binnen 72h”), ISO 27701 helpt bij de uitvoering en borging hiervan.

## Risicogedreven PDCA-implementatie van een PIMS

Onderstaand stappenmodel volgt de Plan-Do-Check-Act cyclus, toegespitst op privacy. De flowchart visualiseert de hoofdlijnen: een permanente risicohouding, managementbetrokkenheid, en herhaling met verbetering【14†L2318-L2326】【26†L278-L287】.

```mermaid
flowchart TD
    A([Start PIMS-initiatief]) --> B{Context & scope vastleggen}
    B --> C[Risico-eigenaren benoemen, stakeholders in kaart brengen]
    C --> D[Risicoanalyse & DPIA-kaders opstellen]
    D --> E[SoA+/Privacybeleidsplan ontwikkelen]
    E --> F[Privacymaatregelen implementeren]
    F --> G[Operationeel beheer: DPIA's, verwerkers, beveiliging]
    G --> H[Monitoren en auditen (CA: DPIA-controles, audits)]
    H --> I[Management review en updates]
    I --> J{Is PIMS effectief?}
    J -- Ja --> K[PIMS certificering / hercertificering voorbereiden]
    J -- Nee --> L[Verbetermaatregelen & CAPA]
    L --> D
    K --> I
```

### Plan (Initiatie en scope)

**Doel:** Leg bestuurlijk vast wat het PIMS omvat en hoe het past binnen de organisatie, op basis van wettelijke vereisten en risicohouding【14†L2318-L2326】【22†L2955-L2963】. 

**Activiteiten:**  
- Bestuurlijke besluitvorming (mandaat, doelstelling PIMS, rol FG/DPO en privacybeleid).  
- Scope & context bepalen: welke data en processen vallen onder het PIMS? Breng bedrijfstakken (bijv. klantenservice, HR, zorgadministratie) en locaties in kaart.  
- Stakeholderanalyse: interne (IT, juridische afdeling, business units) en externe (toezichthouders, ketenpartners) definiëren.  
- Compliance mapping: inventariseer relevante regelgeving (GDPR, lokale wetten, contractuele eisen) en ISO-27701-vereisten. Verbind deze met de geplande PIMS-maatregelen. ([4†L33-L41])  
- Opzetten PIMS-governancestructuur: benoem PIMS-team (DPO, privacy officer, IT-security, jurist), RACI voor besluiten en escalaties.  

**Rollen/competenties:**  
- **Directie/MT** (mandaat, middelen).  
- **DPO/FG** (privacy-expert, nexus privacy-IT).  
- **CISO/InfoSec** (beveiligingskennis, ISMS).  
- **Juridische/compliance** (AVG-kennis).  
- **Proces- en datacoördinatoren** (domeinkennis van persoonsgegevens).  
- **Data-protection committees** (alle stakeholders).

**Deliverables:**  
- PIMS-charter (mandaat, scope, doelen).  
- Stakeholder- en wetgevingsmatrix (bijv. tabel met AVG-artikelen vs interne requirements).  
- Risico- en complianceregister (inclusief datacategorieën, DPIA-plichtige verwerkingen).  
- Rollenmatrix (RACI) van PIMS-borging.  

**Tijdsindicatie:**  
- **Klein:** ~2–4 weken (weinig processen, directieteam snel in beslis).  
- **Middel:** ~4–8 weken (meerdere divisies, externe input nodig).  
- **Groot:** ~8–12 weken (matrixorganisatie, veel stakeholders)【14†L2318-L2326】.  

**Middelen/tools:** organisatiechart, stakeholder/interessentenlijst, compliance-software of Excel, projectmanagementtool.

**Risico’s/mitigaties:**  
- Onvoldoende mandaat ⇒ escaleren naar MT, dwingende AVG-redenen.  
- Onvolledige scope (lekkage tussen afdelingen) ⇒ workshop afdelingshoofden.  
- Gebrek aan betrokkenheid IT/beveiliging ⇒ betrek early, koppel aan NIS2/governance.  

**Succescriteria:**  
- Bestuur/governance heeft PIMS officieel goedgekeurd.  
- Volledige set privacy- en beveiligingseisen geëxpliciteerd (ISO 27701 annex + GDPR-artikelen).  
- Roles & responsibilities zijn gecommuniceerd en geaccordeerd.

### Do (Implementatie van privacymaatregelen)

**Doel:** Implementeer de gekozen privacycontroles en procedures zoals vastgelegd in beleid, en veranker ze in de operatie. Denk hierbij aan AVG-vereisten zoals DPIA en datalekbeheer【14†L2318-L2326】【28†L2484-L2492】. 

**Activiteiten:**  
- **Privacybeleid en procedures**: opstellen of aanpassen (bv. privacyverklaring, DPIA-procedure, privacy-by-design checklist, gegevensverwerkersbeleid).  
- **Data-inventarisatie**: compleet maken van het verwerkingsregister (wie, wat, waarom), evt. scoping van persoonsgegevens (PII-classificatie).  
- **DPIA-proces inrichten**: werkmethodiek (screeningformulier, templates) en toetsing invoeren; evalueer bestaande DPIA’s en vul aan waar nodig【28†L2484-L2492】.  
- **Verwerkersbeheer**: contracten/AV-overeenkomsten actualiseren met privacyclausules (Art.28 GDPR), leverancierssegregatie, security-eisen afdwingen.  
- **Beveiliging van persoonsgegevens**: technische maatregelen (encryptie, pseudonimisering, toegangscontrole, logging, incidentresponse) en organisatorische (toegangsbeleid, awareness/training, noodplannen) implementeren, in lijn met Art.32.  
- **Dataminimalisatie en retentie**: beleid opstellen voor opslag, anonimiseren, vroege vernietiging van niet-nodige data.  
- **Incident- en brechthandling**: meldingsproces inrichten (melding aan AP binnen 72 uur【14†L2318-L2326】, intern proces voor breach-onderzoek), inclusief forms en escalaties.  
- **Awareness en training**: scholingsprogramma’s privacy voor alle lagen (van MT tot uitvoerenden).  
- **Automatisering**: indien mogelijk PIMS/GRC-tool inzetten voor documentatie (PIMS-modules, DPIA-tools, workflow).  

**Rollen/competenties:**  
- **IT-beheer/Security** (technische controls, logging, patchbeheer).  
- **Informatie-eigenaren / Procesmanagers** (vaststellen verwerkingsdoelen, beoordelen DPIA).  
- **Privacy Officer / DPO** (overzicht wetgeving, DPIA-begeleiding).  
- **Contractmanager / Inkoop** (verwerkerscontracten, vendor assessment).  
- **Awareness Trainer / HR** (trainingen, handhaving).  

**Deliverables:**  
- Geactualiseerd privacybeleid (incl. DPIA-beleid, datalekbeleid, inzage-beleid).  
- Compleet verwerkingsregister (templatelijst).  
- DPIA-rapporten en checklist/overzicht DPIA-plichtige verwerkingen.  
- Werkinstructies privacy (bijv. voor dataretentie, data-anonimiseren).  
- Aangepaste verwerkersovereenkomsten en verwerkerslijst.  
- Rapportage maatregelen (encryptie, MFA-status, logging coverage).  
- Evidence portfolio (logs, trainingregistratie, patchrapporten, audit logs).  

**Tijdsindicatie:**  
- **Klein:** ~3–6 maanden (weinig data, eenvoudige processen).  
- **Middel:** ~6–12 maanden (meerdere businessunits, veel verwerkers).  
- **Groot:** ~9–18 maanden (geconsolideerde projecten, ingewikkelde ICT).  
(Onzekerheid: afhankelijk van beginsituatie en beschikbare middelen. Bij aanwezigheid van een ISMS gaat dit vaak sneller.)【26†L278-L287】  

**Middelen/tools:**  
- **GRC/PIMS-systeem** (risico- en beleidsmanagement, DPIA-module, incident registratie).  
- **IT-security tools** (IAM/MFA, DLP, logging/SIEM, encryption).  
- **Document management** (versiebeheer), **workflowsysteem** (tickets voor DPIA, meldingen).  
- **Templatebibliotheek** voor contracten, procedures, DPIA- en policy-sjablonen.  

**Risico’s/mitigaties:**  
- **Fragmentarisch beheer (silo’s)** ⇒ centrale PIMS-tool en KPI’s voor dekking alle data-eigenaren.  
- **Project-overload** ⇒ fasering op basis van hoogste risico’s; quick wins (bijv. direct helder-retentiebeleid).  
- **Juridische lacunes** ⇒ DPO laten toetsen en AP-richtlijnen raadplegen (bijv. EDPB DPIA-richtlijnen).  

**Succescriteria:**  
- ≥95% van kritieke verwerkingen zijn voorzien van actuele DPIA (indien vereist) en bijbehorende maatregelen.  
- Er is formeel beleidsdocument over privacysysteem dat is geaccepteerd en verspreid.  
- Technische maatregelen (encryptie, backups, logging) zijn operationeel en getest.  
- Monitoring toont voldaan: bijvoorbeeld 100% datalekmeldingen binnen 72 uur (GDPR eisen) of vermindering aantal privacy-incidenten.  

### Check (Monitoren & Auditeren)

**Doel:** Bevestigen dat het PIMS werkt: controles en processen doen wat ze moeten doen, afwijkingen signaleren en verantwoording kunnen afleggen (zg. “governance evidence”).  

**Activiteiten:**  
- **Performance monitoring**: KPI’s instellen en bijhouden (bv. aantal gehonoreerde AR-verzoeken, aantal datalekmeldingen, aantal verwerkte DPIA’s, training compliance).  
- **Interne audit Privacy**: onafhankelijke toets van het PIMS-programma (compliance met ISO 27701 en AVG), inclusief controles op de hogere ritmes. Auditprogramma opstellen (bijv. jaarlijkse cyclus) en bevindingen opvolgen.  
- **Management Review**: formeel periodiek overleg (directiebijeenkomst) waarin PIMS-resultaten, risico’s, incidenten en verbeteracties worden besproken.  
- **DPIA-herziening**: regelmatig herzien DPIA’s bij veranderingen (Art.39 AVG vereist periodieke review)【28†L2593-L2599】.  
- **Incident lessons learned**: datalekken en klachten systematisch analyseren en terugkoppelen in verbeteringen.  
- **Surveillances / Toezichthouders**: voorbereiden op mogelijk AP‑ of externe audit (doorgaans elke 1-3 jaar).  

**Rollen/competenties:**  
- **Internal audit team** of auditor (onafhankelijk toetsen ISO/GDPR).  
- **PIMS-/Privacy-manager** (draagt rapportages over).  
- **Data Owners/DPO** (uitvoeren van audits en acties).  
- **Management/Directie** (besluiten gebaseerd op rapportage).  

**Deliverables:**  
- Auditprogramma en interne auditrapportages (met corrigerende maatregelen).  
- Managementreviewnotulen + besliste actiepunten.  
- KPI-rapportage dashboard.  
- Geactualiseerde risico- en SoA-documenten na uitkomsten.  

**Tijdsindicatie:**  
- Initiële monitoringcyclus: **Klein** ~1–2 maanden opzetten, dan  quarterly/halfjaarlijks; **Middel** ~2–3 maanden, **Groot** ~3–6 maanden (inclusief toolconfiguratie).  
- Recurrence: audit- en reviewcycli per jaar of vaker na grote incidenten.  

**Middelen/tools:** Audit/GRC-modules, SIEM/monitoring dashboard, enquête/software voor datalek-meldingen, rapportagetools.  

**Risico’s/mitigaties:**  
- **Overdaad aan metrics** ⇒ focus op kritische KPIs (GDPR-impact, risico’s).  
- **Niet opvolgen bevindingen** ⇒ managementrichtlijnen voor CAPA (eventueel SLA voor fix).  

**Succescriteria:**  
- Op alle interne audits en management reviews ontbreekt geen kritieke non-conformiteit (of deze is binnen afgesproken termijn opgelost).  
- Beoordeling toont dat beleidsdoelen (bijv. “90% systemen onder steunen beveiliging”, “⩾x DPIA’s voltooid”) worden gehaald.  
- Ketenprocessen (incidentmelding, DPO-advies) functioneren direct na incident volgens procedures (bewezen via logs).  

### Act (Verbeteren en onderhouden)

**Doel:** Continue bijsturen, lessons learned toepassen en – indien gewenst – externe certificering voorbereiden. De PIMS-cyclus wordt herhaald met update van risico’s en scope.

**Activiteiten:**  
- **Correctieve acties**: na audits/incidenten direct uitvoeren van root cause analyses en procesaanpassingen (bijv. nieuwe techniek, extra training).  
- **Policy updates**: bij wetgevende veranderingen of veranderende risico’s (bijv. nieuwe AVG-handreiking, NIS2) actualiseer beleid en controles.  
- **Herbeoordeling scope**: periodiek scope check, toevoegen/verwijderen dataflows (bijv. nieuwe app, geoutsourcete verwerker).  
- **Certificeringsproces**: voorbereiding (Stage 1-audit: document review, Stage 2: bewijsvoering op locatie) als organisatie streeft naar ISO 27701-certificaat. Dit omvat vaak een pre-audit assessment en aantekening van de Scope (zoals Samoerai beschrijft【3†L49-L52】).  
- **Cultuur en training**: continue privacybewustzijn (learnings uit lessons, herhaalde training).  
- **Verankeren in business**: integratie van privacyrichtlijnen in projectmanagement (privacy by design), inkoop en contracten (privacyclausules standaard).  

**Rollen/competenties:**  
- **Alle stakeholders** actief (verantwoordelijk voor afhandeling CAPA uit eigen gebied).  
- **PIMS-coördinator/DPO** (borgt overall continuïteit, rapporteert aan MT).  
- **Auditor** (hercertificering, toezicht).  

**Deliverables:**  
- Verbeterregister (CAPA met status).  
- Aangepaste risico- en opleidingsplannen.  
- Certificeringsrapport of bewijs van naleving (indien van toepassing).  

**Tijdsindicatie:**  
- Loop per jaar; certificeringstraject ~3–6 maanden na goede interne audit (externe auditplanning afhankelijk van certificerende instellingen).  
- Continue: onmiddellijke actie na elk incident/audit.  

**Succescriteria:**  
- Trendmatige verbetering in KPI’s en auditresultaten.  
- Duidelijke toename in privacymaturiteit (bijv. 3rd-party assessment, ISO 27701-status).  
- Positieve externe beoordeling (NEN, AP-check, certificaat behaald).

## Deliverables en templates

Onderstaande tabel geeft overzichtelijke kern-deliverables per fase, inclusief voorbeeldinhoud en verantwoordelijke rollen. Gebruik dit als checklist. 

| Deliverable               | Fase            | Inhoud (template voorbeelden)                         | Verantwoordelijke  | Bewijsbasis/Te tonen                 |
|---------------------------|-----------------|-------------------------------------------------------|--------------------|--------------------------------------|
| **PIMS-charter/beleid**   | Initiatie (Plan) | Doelstelling PIMS, scope, mandaat, bestuurlijke rollen, risicobereidheid【3†L49-L52】 | MT / PIMS-team     | Officieel besluit (BB/Vaststelling)  |
| **Stakeholder- en compliance register** | Initiatie (Plan) | Lijst wetgeving (GDPR-artikelen, NIS2, UAVG) + interne eisen; stakeholders en verantwoordelijkheden. | DPO / CISO         | Volgt uit interviews, workshopverslagen |
| **Verwerkingsregister**   | Do (Implement.) | Gedetailleerd overzicht van verwerkingen: categorie persoonsdata, doel, rechtsgrond, bewaartermijn, betrokken partijen. | Privacy Officer    | Afgedrukt register, log data-elevering |
| **DPIA-rapport(en)**      | Do / Check      | Risicoanalyse+mitigatie van risicovolle verwerking(en); vragenlijst & resultaat. | Procesowner/DPO    | Beoordelde DPIA-documenten            |
| **Statement of Applicability (SoA+)**  | Do (Plan/Implement.) | Relatie tussen ISO 27701 controls en GDPR-eisen; wel/niet toepasbaar en motivatie【22†L2955-L2963】. | PIMS-manager      | SoA met gekoppelde bewijzen           |
| **Privacyimpact (DPIA)-procedure** | Do (Plan) | Stappenplan DPIA: triggers (Art.35), intake, advies FG, reviewmomenten. | DPO / Jurist       | Definitiedocument proces              |
| **Verwerker- en contractoverzicht** | Do (Implement.) | Lijst verwerkers + contractstatus; sjabloon verwerkersovereenkomst (AVG-compliant clausules). | Inkoop / Legal     | Ondertekende contracten               |
| **Beveiligingspolicy PII**| Do (Implement.) | Richtlijnen encryptie, authn/authz, dataminimalisatie, incidentresponse (i.v.m. GDPR Art.32). | CISO / DPO         | Gearchiveerd beleidsdocument          |
| **Training materials**    | Do (Implement.) | Privacy awareness presentaties, e-learningmodules (inzicht AVG-basisprincipes, plichten). | HR / Security Team | Trainingregistratie, certificaten     |
| **Internal auditrapporten** | Check         | Bevindingen-rapport op PIMS/GDPR compliance; aanbevelingen (met actieplan). | Internal auditor   | Auditverslag + CAPA-tracker           |
| **Management review verslagen** | Check      | Overzicht KPI’s, auditinzichten, risico’s, besluitvorming. | MT / DPO           | Notulen met besluiten                |
| **Privacy maturity-rapport** | Act         | Maturiteitsmeting (bijv. CMM of interne checklist) ten opzichte van doel (committment). | PIMS-team          | Rapportage + improvement roadmap      |

*Templates* voor bovengenoemde deliverables kunnen inhouden: statische Word-/Excel-sjablonen óf dynamische records in een GRC/PIMS-tool (aanbevolen). Bijvoorbeeld: een DPIA-sjabloon met verplichte velden (beschrijving, risico-inschatting, maatregelen), een contracttemplate met AVG-clausules, en een standaard SoA-format dat elk control item uit ISO 27701 koppelt aan AVG-artikelen. Zorg dat alle templates versienummering en bevestiging door verantwoordelijken hebben.

## Rollen, competenties en verantwoordelijkheden

Een effectief PIMS vergt samenwerking over functies heen. Belangrijke rollen zijn:

- **Data Protection Officer (DPO/FG)** – *privacyexpert*, adviseert in design, bewaakt kwaliteit DPIA’s, eerste aanspreekpunt voor toezicht (UAVG voorschrijft meldplicht/lichaamskracht)【3†L49-L52】.  
- **PIMS-manager / Privacy Officer** – brengt ritme aan, monitort voortgang, onderhoudt registers, wijst acties toe.  
- **CISO / Security Lead** – levert technische maatregelen (encryptie, logging, netwerkbeveiliging) en koppelt PIMS aan het bredere ISMS.  
- **Proces- en dataverantwoordelijken** – *aanwijzen wat, waarom en hoe* van dataverwerking (bijv. Manager Klantgegevens, HR, financiën). Zij voeren DPIA’s uit en ondersteunen audits.  
- **Juridische/compliance afdeling** – vertaalt wetgeving naar beleid/contracten, toetst privacybeleid en verwerkersovereenkomsten op wettelijke adequaatheid.  
- **Leveranciersmanager / Inkoop** – zorgt voor security/privacy-eisen in RFI/PvE en contracten, monitort naleving.  
- **IT/Dev/Ops team** – implementeert technische controls, ondersteunt bij dataklassificatie en incident response.  
- **Training/HR** – verzorgt bewustwordingstrainingen en borgt dat (nieuw) personeel de procedures kent.  

Kleinere organisaties combineren vaak rollen (bijvoorbeeld DPO=CISO), grote laten ze los (volledige teams). Een RACI-tabel kan helder maken wie verantwoordelijk/is voor wat in elke fase (zie Deliverables-tabel).

## Tooling en middelen

**GRC/PIMS platforms:** Er zijn gespecialiseerde privacy- en GRC-tools (bijv. SmartManSys, OneTrust, TrustArc) die verwerkingsregisters, DPIA’s, contractmanagement, incidentmanagement en rapportages integreren. Deze zorgen voor één centrale “single source of truth” en automatische workflow (bijv. bij een datalek direct melding naar DPO). 

**Identiteits- en toegangsbeheer (IAM):** MFA en role-based access control beperken gegevens exposure (GDPR art.32).  
**Encryption & pseudonimisering:** Cruciaal voor dataminimalisatie en data security (Art.32).  
**SIEM/logging:** Detecteert en logt toegang/datalek-incidenten, waarmee voldoen aan ‘regelen testen en evalueren’【14†L2318-L2326】.  
**ITSM/incident tooling:** Voor registratie van privacy-gerelateerde incidenten en opvolging, aansluiten op datalekmelding.  
**Awareness & opleidingsplatforms:** Voor continious training van medewerkers.  
**Document Management System:** Voor beveiligd bewaren en versiebeheer van PIMS-documentatie (beleid, contracten, auditlogs).  
**Checklists/Dashboards:** Voor real-time dashboards (bijv. % afgeronde DPIA’s, backlog verwerkersovereenkomsten) en compliance-checklists (bijv. ISO-27701 self-assessment) om voortgang meetbaar te maken.

Essentieel is: voorkom tool-silo’s. Laat systemen data delen (bv. koppeling HR-systemen met PIMS-tools voor rolupdates). Technologie ondersteunt het proces, maar gedraagt zich niet vanzelf; governance staat voorop.

## Implementatieroadmap en varianten

De implementatie is fasegewijs. De onderstaande Gantt toont één mogelijke volgorde; tijdsblokken zijn indicatief (startdata/budget onduidelijk, varieert sterk met grootte/maturiteit).

```mermaid
gantt
    title PIMS Implementatie Roadmap
    dateFormat  YYYY-MM-DD
    axisFormat  %b %Y

    section Voorbereiding
    Governance & mandate            :done,    des1, 2026-04-01, 30d
    Stakeholders & scope define    :done,    des2, 2026-04-15, 30d

    section Risicogebaseerde planning
    Data-inventarisatie & DPIA-scan:         des3, after des2, 45d
    Risicomanagementkader opstellen :         des4, after des3, 30d

    section Implementatie controls
    Privacybeleid & procedures     :         des5, after des4, 60d
    DPIA en Verwerkersprocessen     :         des6, parallel des5, 60d
    Technische beveiliging (MFA, enc, logging) : des7, after des4, 60d
    Awareness en training          :         des8, after des5, 45d

    section Operating
    Incident- & breachmanagement   :         des9, after des7, 30d
    Verwerkers- en contractbeheer  :         des10, after des6, 30d

    section Controleren & verbeteren
    Monitoring & audits (1e cyclus):         des11, after des9, 45d
    Management review & updates    :         des12, after des11, 30d
    CAPA & bijsturing              :         des13, after des12, 30d

    section Certificering (optioneel)
    Pre-audit & documentatie       :crit,    des14, after des13, 30d
    Stage 1+2 audit ISO 27701      :crit,    des15, after des14, 30d
```

Deze roadmap kan per organisatie **schaalbaar** aangepast worden:

- **Klein** (bijv. enkele tientallen medewerkers): weinig gescheiden data-stromen, minder formele rollen. Start eenvoudig: gebruik beschikbare sjablonen, focus op sleutelverwerkingen. Tijdsindicatie ~6–9 maanden totaal. Maak gebruik van handige tools (bv. gecombineerde ISMS/PIMS-software) om overhead laag te houden.  
- **Middel** (100–500 medewerkers): meerdere afdelingen, enkele DPO’s, bestaande ISMS. Hier is structureren van eigenaarschap belangrijk. Reserveer ~9–12 maanden voor livegang van alle routines. Voeg tooling als audit modules toe om efficiency te verhogen (bijv. GRC).  
- **Groot** (>500 medewerkers, complexe ketens): mogelijk meerdere dochterbedrijven of diensten. Loop dit proces top-down uit: per business unit of locatie een mini-PIMS onder centrale governance. Fasering kan per business lines. Gemiddeld 12–18 maanden, afhankelijk van automatiseringsgraad. Certificeringtraject tijdig inplannen (soms volg- of combinatiecertificering met ISO 27001). 

In alle gevallen geldt: in een gemeente of publieke organisatie kan ENSIA gebruikt worden voor integrale verantwoording. Hierbij wordt het PIMS-bewijs opnieuw gebruikt om toezichthouders en raad te informeren, zodat er **“one stop compliance”** ontstaat voor security én privacy. Bijvoorbeeld kan het PIMS-beleidsplan samenvallen met het gemeentelijk privacy- en securitybeleid.

## Praktijkvoorbeelden

- **Gemeentelijke samenwerking ISO/PIMS:** Enkele gemeenten hebben ISO 27001/27701 ingezet voor AVG-compliance. Zij ontdekten dat hergebruik van ISMS-processen (audits, risicoregister) de implementatielast reduceerde, en dat leverancierskeuzes (bijv. hosting op ISO 27001/27701-gecertificeerde cloud) toenamen.  
- **Zorginstelling:** Bij een grote zorginstelling (personenbeschermd) leidde een PIMS tot verbeterd beleid voor e-health-apps; DPIA-vereisten werden strak ingepland, wat datalekken afbreuk minimaliseerde.  
- **Industrieel bedrijf:** Een multinational gebruikte ISO 27701 om wereldwijd een datalekprocedure te harmoniseren. Het hielp consistentie in verwerkerscontracten en maakte datalekmeldingen auditklaar, wat de Nederlandse AP overtuigde dat er ‘passende maatregelen’ stonden (AP-straal).  

Deze voorbeelden tonen aan dat PIMS/ISO-certificering niet alleen compliance-tooling is, maar ook (vooral voor grotere organisaties) een selectiecriterium kan worden voor klanten en partners (conform ADM en klantvraag【26†L272-L279】【3†L49-L52】).

---

**Bronnen:** In deze rapportage zijn voor **Nederlandse en EU-wetgeving** en best practices geput uit officiële documenten (EUR-Lex, ENISA, NCSC, NCTV, ISO- en NEN-overzichten) en erkende publicaties【14†L2318-L2326】【22†L2955-L2963】【3†L49-L52】【26†L278-L287】. De praktijkvoorbeelden en adviezen zijn afgeleid van geciteerde cases en richtlijnen uit de sector. (Verdieping in AP-handreikingen en NIST Privacy Framework kan aanvullend nuttig zijn.)
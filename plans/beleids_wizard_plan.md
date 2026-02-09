# Beleids-Wizard: Interactieve Workflow Ontwerp

Dit document beschrijft het ontwerp en de functionele workflow voor de "Beleids-Wizard" binnen het IMS. Het doel is om gebruikers te begeleiden bij het schrijven van beleid dat voldoet aan specifieke standaarden.

## Concept: De "Policy Flow" Wizard

De Wizard transformeert de abstracte taak van "beleid schrijven" naar een gestructureerde, interactieve ervaring. Het fungeert als een intelligente gids die de gebruiker van een leeg vel naar een volledige beleidsconcept brengt.

---

## 1. De Trechter (Inputfase)

### Stap 1: Domein Selectie
De gebruiker kiest in eerste instantie de toepassing:
- 🛡️ **Informatiebeveiliging (Security):** Focus op vertrouwelijkheid, integriteit en beschikbaarheid (ISO 27001, BIO).
- ⚖️ **Privacy (AVG/GDPR):** Focus op persoonsgegevens, rechten van betrokkenen en dataminimalisatie.
- 🔄 **Business Continuity (BCM):** Focus op veerkracht, hersteltijden en kritieke processen.
- 🌐 **Integraal Beleid (IMS Combi):** Voor het gelijktijdig dekken van alle drie de domeinen.

### Stap 2: Normbepaling (Input & Analyse)
De gebruiker bepaalt aan welke standaarden voldaan moet worden:
- **Lijstkeuze:** Selecteer bekende standaarden (bijv. ISO 27001, NEN 7510, BIO).
- **Prompt-gestuurd:** Vertel de AI de specifieke context (bijv. "Ik ben een zorginstelling en moet voldoen aan de strengste privacyregels").
- **Output:** De Wizard identificeert direct de relevante hoofdstukken en verplichte beheersmaatregelen.

---

## 2. De Architectuur-Check (De 'Splitsen of Samenvoegen' check)

Zodra de standaarden zijn geïdentificeerd, adviseert de assistent over de beste structuur:

1.  **Analyse:** "Je moet aan X beheersmaatregelen voldoen. Dit is een omvangrijk pakket."
2.  **Keuze:**
    *   **Optie A: Integraal Beleid.** Alles in één (handig voor kleine organisaties).
    *   **Optie B: Modulair Beleid (Aanbevolen).** Opsplitsen in logische brokken (bijv. apart 'Personeelsbeleid', 'Wachtwoordbeleid').
3.  **Advies:** De assistent stelt vragen over de doelgroep en organisatiegrootte om de beste keuze te maken.

---

## 3. De Interactieve Workflow (Uitvoering)

De AI bouwt een dynamische roadmap op basis van de gemaakte keuzes:

| Fase | Actie van de Wizard | Gebruikersinput |
| :--- | :--- | :--- |
| **1. Scope** | Definieert toepassingsgebied. | "Geldt dit voor de hele organisatie?" |
| **2. Context** | Analyseert huidige situatie. | "Welke kritieke systemen gebruiken jullie?" |
| **3. Maatregelen** | Stelt teksten voor o.b.v. norm. | "Keur deze concepttekst over wachtwoordbeleid goed." |
| **4. Validatie** | Checkt compliance gap. | Feedbackronde o.b.v. ontbrekende norm-onderdelen. |

### De 'Compliance Tracker'
In de zijbalk ziet de gebruiker voortdurend de voortgang: *"Je dekt nu 15% van de ISO-norm."*

---

## 4. Speciale Logica: Integraal Management Systeem (IMS)

Wanneer gekozen wordt voor meerdere domeinen, activeert de **Master Mapper**:
- **Kruisbestuiving:** Overlappende onderwerpen (zoals Incident Management) worden samengevoegd.
- **Consistentie:** Voorkomt tegenstrijdige regels tussen Security en Privacy.
- **Thematische Modules:** Advies om te werken met modules als 'Organisatie & Mensen' versus 'Techniek'.

---

## Voordelen van deze Aanpak

1.  **Drempelverlagend:** Geen "Writer's Block". Gebruikers beantwoorden vragen; de AI formuleert.
2.  **Compliance by Design:** De norm is de kapstok; verplichte onderdelen kunnen niet vergeten worden.
3.  **Flexibiliteit:** Ondersteunt zowel monolithische als modulaire documentatie.
4.  **Onderhoudbaarheid:** Bij wetswijzigingen hoeft alleen de relevante module aangepast te worden.

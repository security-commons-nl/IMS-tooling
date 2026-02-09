# IMPROVE RISK TOLERANCE AND DECISIONS

## Concept: Dynamische Risico-instelling & Matrix Visualisatie

Het doel is om een centraal dashboard te creëren waar de directie de **Risk Appetite** (risicotolerantie) bepaalt, waarna deze automatisch de grenzen in de risicomatrix voor de hele organisatie verlegt.

### 1. Centrale Configuratie (De 'Knoppen')

In plaats van statische tekst, krijgt de organisatie een instellingenpaneel per risicocategorie. Voor elke categorie wordt de tolerantie bepaald op een schaal (bijv. 1-5 of 'Avers' tot 'Opportunistisch').

*   **Operationeel:** Focus op continuïteit (downtime).
*   **Juridisch:** Focus op compliance (boetes/wetgeving).
*   **Reputatie:** Focus op publieke perceptie.
*   **Financieel:** Focus op budget en cashflow.

### 2. Visuele Integratie in de Matrix

Wanneer een medewerker een risico opvoert, ziet deze de standaard matrix (Kans × Impact). De ingestelde tolerantie wordt hier direct zichtbaar gemaakt:

*   **De 'Heatmap' verschuift:** De groene (acceptabele) zone wordt groter of kleiner op basis van de Risk Appetite.
*   **Drempelwaarden:** Een visuele grens (stippellijn/schaduw) toont de tolerantie.
*   **Real-time feedback:** Melding als een risico buiten de tolerantie valt.

---

## Gedetailleerd Rekenmodel: Financiële Categorie

Dit model beschrijft hoe een financiële Risk Appetite (bijv. "€50.000") zich vertaalt naar de 4x4 matrix.

### A. Definieer de Impact-schaal (Statisch of Dynamisch)

De X-as van de matrix (Impact) moet eerst gekwantificeerd worden.

| Score | Impact Niveau | Financiële Range (Voorbeeld) |
| :--- | :--- | :--- |
| **1** | **Laag** | < € 10.000 |
| **2** | **Middel** | € 10.000 - € 100.000 |
| **3** | **Hoog** | € 100.000 - € 500.000 |
| **4** | **Kritiek** | > € 500.000 |

### B. Definieer de Risk Appetite (De Instelling)

De organisatie kiest een **Appetite Level** voor Financieel.

| Appetite Level | Beschrijving | Maximaal Acceptabel Verlies (Single Event) |
| :--- | :--- | :--- |
| **1. Avers** | Risicomijdend | € 10.000 (Impact 1) |
| **2. Voorzichtig** | Beperkt risico | € 50.000 (Impact 2 - ondergrens) |
| **3. Gematigd** | Balans | € 100.000 (Impact 2 - bovengrens) |
| **4. Open** | Risicozoekend | € 250.000 (Impact 3 - ondergrens) |
| **5. Speculatief** | Hoge winst/verlies | > € 500.000 (Impact 4) |

### C. Vertaling naar de Matrix (De Heatmap)

De **Risk Appetite Threshold** bepaalt de grens tussen **Groen (Accepteren)** en **Oranje/Rood (Mitigeren)**.

Formule: *Als (Kans × Impact) ≤ Threshold, dan Groen.*
Echter, bij Risk Appetite gaat het vaak puur over de **Impact** die men kan dragen, ongeacht de kans. Een kritiek risico (Impact 4) is vaak onacceptabel, zelfs bij kleine kans, tenzij de appetite "Speculatief" is.

**Model voor dynamische kleuring:**

We introduceren een **"Acceptatie Grens"** in de matrix.

*   **Scenario: Appetite = Avers (Max €10k)**
    *   Impact 1 (Laag): Acceptabel (Groen)
    *   Impact 2, 3, 4: Onacceptabel (Oranje/Rood), ongeacht de kans.
    *   *Visueel:* Alleen de linkerkolom (Impact 1) is groen.

*   **Scenario: Appetite = Gematigd (Max €100k)**
    *   Impact 1 (Laag): Altijd Groen.
    *   Impact 2 (Middel): Groen (want < €100k).
    *   Impact 3, 4: Oranje/Rood.
    *   *Visueel:* De eerste twee kolommen zijn groen.

*   **Scenario: Appetite = Open (Max €250k)**
    *   Impact 1, 2: Altijd Groen.
    *   Impact 3 (Hoog): Acceptabel mits Kans laag is (bijv. Kans 1 of 2).
    *   *Visueel:* Kolom 1 & 2 zijn groen. Kolom 3 is groen in de onderste helft (Kans 1-2).

### D. User Interface Implicaties

1.  **Slider voor Bedrag:** De gebruiker stelt een bedrag in (bijv. € 50.000).
2.  **Mapping:** Het systeem kijkt in welk Impact-bucket dit valt (Bucket 2: €10k-€100k).
3.  **Visualisatie:** De matrix tekent een verticale lijn tussen Impact 2 en 3. Alles links daarvan is "binnen mandaat".
4.  **Uitzonderingen:** "Kans" speelt een rol. Zelfs als het bedrag binnen de appetite valt, kan een *zeer hoge kans* (bijv. dagelijks) het onacceptabel maken voor de operatie.
    *   *Regel:* Als Kans = 4 (Zeer Groot), dan ALTIJD Mitigeren/Escaleren, tenzij Impact = 1.

---


## Tech Stack & Implementatie Details

### 1. Backend: RiskFramework Uitbreiding
*   **Bestand:** `backend/app/models/core_models.py`
*   **Model:** `RiskFramework`
*   **Wijziging:** We gebruiken het bestaande `risk_tolerance` JSON-veld. We definiëren een strikte structuur:
    ```json
    {
      "financial": {
        "threshold_value": 50000,
        "appetite_level": "MODERATE", // Enum: AVERSE, CAUTIOUS, MODERATE, OPEN, HUNGRY
        "impact_correlation": {
            "1": 10000,   // Impact 1 < 10k
            "2": 100000,  // Impact 2 < 100k
            "3": 500000,  // Impact 3 < 500k
            "4": 1000000  // Impact 4 > 500k
        }
      },
      "legal": { ... },
      "reputation": { ... }
    }
    ```
*   **API:** `backend/app/api/v1/endpoints/risk_framework.py` - Geen wijzigingen nodig, update werkt al op JSON velden.

### 2. Frontend: Instellingen UI
*   **Bestand:** `frontend/ims/pages/organization.py` (of nieuw `frontend/ims/pages/framework_settings.py` als het te groot wordt).
*   **State:** `RiskFrameworkState` aanmaken of toevoegen aan `OrganizationProfileState`.
*   **Componenten:**
    *   Sliders voor bedragen (Financieel).
    *   Dropdowns voor Appetite Levels.
    *   Visualisatie "Preview" van de matrix (klein) die meekleurt.

### 3. Frontend: Dynamische Heatmap
*   **Bestand:** `frontend/ims/components/heatmap.py`
*   **Logica:**
    *   De huidige statische `grid` vervangen door een dynamische rendering.
    *   Injecteren van `RiskFramework` data in de component.
    *   **Tolerance Line:** Een visuele grens tekenen (bijv. border tussen kolommen 2 en 3).
    *   **Opaciteit:** Cellen die 'buiten appetite' vallen helderder maken, binnen appetite iets dimmen (of andersom).

### 4. Frontend: Risk State & Validatie
*   **Bestand:** `frontend/ims/state/risk.py`
*   **Wijziging:**
    *   Bij `load_risks`, ook het actieve `RiskFramework` inladen.
    *   Computed var `is_risk_acceptable(score, category)` toevoegen.
    *   Bij het opslaan/wijzigen van een risico: waarschuwing tonen als `inherent_score > tolerance`.

---

## Implementatie Stappenplan

1.  **Backend Configuratie**
    *   [ ] Maak een helper script/functie om een default `RiskFramework` met de nieuwe JSON structuur te seeden (zodat we data hebben om mee te testen).
    *   [ ] Verifieer dat de `RiskFramework` API correct JSON opslaat en teruggeeft.

2.  **Frontend State**
    *   [ ] Maak `frontend/ims/state/risk_framework.py` voor het laden/updaten van het framework.
    *   [ ] Integreer dit in `frontend/ims/state/risk.py` zodat risico's hun context kennen.

3.  **Frontend UI - Settings**
    *   [ ] Bouw de "Appetite Slider" component.
    *   [ ] Voeg deze toe aan een nieuwe tab in `frontend/ims/pages/organization.py`.

4.  **Frontend UI - Heatmap**
    *   [ ] Pas `quadrant_cell` aan in `heatmap.py` om styling parameters (kleur, border) te accepteren.
    *   [ ] Implementeer de logica die bepaalt welke cellen "In Appetite" zijn op basis van de slider-waarde.


# Plan: Mijn Organisatie — Tooltips + AI-Prefill

## Doel

Twee verbeteringen aan de onboarding wizard op `/organization`:

1. **Tooltips bij vakjargon** — uitleg van termen én gradaties (laag/midden/hoog)
2. **AI-prefill na stap 1** — op basis van Identiteit automatisch voorzet doen voor stap 2–6

---

## Wijziging 1: Tooltips bij velden

### Welke velden krijgen tooltips?

| Stap | Veld | Tooltip-inhoud |
|------|------|----------------|
| Governance | Governance volwassenheid | Uitleg CMM-niveaus: Startend (ad hoc, geen formeel beleid) → Basis (basale processen) → Gedefinieerd (gedocumenteerd) → Beheerst (gemeten & gestuurd) → Geoptimaliseerd (continu verbeterend) |
| Governance | Risicobereidheid — Beschikbaarheid | "Hoeveel uitval accepteert uw organisatie?" Laag = minimaal risico acceptabel, systemen moeten altijd beschikbaar zijn. Midden = beperkte uitval acceptabel (uren). Hoog = langere uitval acceptabel (dagen). |
| Governance | Risicobereidheid — Integriteit | "Hoeveel risico op onjuiste data accepteert uw organisatie?" Laag = data moet altijd 100% correct zijn. Midden = incidentele fouten acceptabel mits herstelbaar. Hoog = fouten acceptabel, geen directe impact. |
| Governance | Risicobereidheid — Vertrouwelijkheid | "Hoeveel risico op ongeautoriseerde toegang accepteert uw organisatie?" Laag = nultolerantie op datalekken. Midden = beperkt risico acceptabel met maatregelen. Hoog = openbare data, weinig gevoeligheid. |
| IT-Landschap | Cloud strategie | On-premises = alles in eigen beheer. Hybrid = mix van eigen infra en cloud. Cloud-first = cloud tenzij er een reden is voor on-prem. Full-cloud = alles in de cloud. |
| IT-Landschap | BYOD | "Bring Your Own Device — mogen medewerkers eigen laptops/telefoons gebruiken voor werk?" |
| Privacy | Bijzondere categorieën | "Verwerkt u gezondheidsgegevens, biometrische data, strafrechtelijke gegevens, politieke voorkeur, religie, etnische afkomst of seksuele geaardheid? (Art. 9 AVG)" |
| Privacy | Internationale doorgifte | "Worden persoonsgegevens buiten de EER verwerkt of opgeslagen? Denk aan cloud-diensten met US-datacenters." |
| Continuïteit | BCP | "Bedrijfscontinuïteitsplan — een gedocumenteerd plan om kritieke processen draaiend te houden bij een calamiteit." |
| Continuïteit | Max toelaatbare downtime | "Hoe lang mag uw primaire dienstverlening maximaal stilliggen? Uren = zeer kritisch. Dag = belangrijk. Week = niet tijdkritisch." |
| Mensen | Bewustwordingsprogramma | "Een structureel programma om medewerkers bewust te maken van informatiebeveiliging en privacy, bijv. phishing-simulaties, e-learning." |

### Technische implementatie

**Frontend: `organization.py`**

Nieuwe helper-functie `form_select_tooltip()` als wrapper rond `form_select()`:

```python
FIELD_TOOLTIPS = {
    "governance_maturity": "Hoe ver is uw organisatie ...",
    "risk_appetite_availability": "Hoeveel uitval ...",
    # etc.
}

def form_select_tooltip(label, value, on_change, options, tooltip_key, **kw):
    """form_select met een info-icoon dat een tooltip toont."""
    tip = FIELD_TOOLTIPS.get(tooltip_key, "")
    return rx.vstack(
        rx.hstack(
            rx.text(label, size="2", weight="medium"),
            rx.tooltip(
                rx.icon("info", size=14, color="gray", cursor="help"),
                content=tip,
                max_width="320px",
            ) if tip else rx.fragment(),
            spacing="1",
            align="center",
        ),
        rx.select(options, value=value, on_change=on_change, ...),
        spacing="1",
        width="100%",
    )
```

Zelfde patroon voor `form_bool_select_tooltip()`.

**Bestanden die wijzigen:**
- `frontend/ims/pages/organization.py` — tooltip-dict toevoegen, form helpers aanpassen, stap-functies updaten

**Geen backend-wijzigingen nodig.**

---

## Wijziging 2: AI-Prefill na stap 1 (Identiteit)

### Concept

Na het opslaan van stap 1 (Identiteit) roept de frontend een nieuw AI-endpoint aan dat op basis van:
- Type organisatie (bijv. "Gemeente")
- Sector (bijv. "Overheid")
- Aantal medewerkers (bijv. "500+")
- Geografische scope
- Kernactiviteiten

…een voorzet genereert voor alle velden van stap 2–6.

### Voorbeeldlogica (Gemeente, Overheid, 500+)

| Veld | Voorgestelde waarde | Rationale |
|------|-------------------|-----------|
| **Governance** | | |
| Certificeringen | — (leeg) | Niet te voorspellen |
| Frameworks | BIO, AVG | Verplicht voor gemeenten |
| Security Officer | Ja | Verplicht bij BIO |
| FG / DPO | Ja | Verplicht bij gemeenten (AVG art. 37) |
| Volwassenheid | Basis | Conservatieve schatting |
| Risico beschikbaarheid | Laag | Publieke dienstverlening = hoge beschikbaarheidseis |
| Risico integriteit | Laag | Basisregistraties moeten accuraat zijn |
| Risico vertrouwelijkheid | Laag | Gevoelige burgerdata |
| **IT-Landschap** | | |
| Cloud strategie | Hybrid | Typisch voor gemeenten |
| Thuiswerken | Ja | Post-COVID standaard |
| BYOD | Nee | Gemeenten gebruiken managed devices |
| IT uitbesteed | Ja | Veel gemeenten besteden IT uit |
| **Privacy** | | |
| Persoonsgegevens | Ja | Gemeenten verwerken altijd persoonsgegevens |
| Betrokkenen | Burgers, Medewerkers | Kernbetrokkenen |
| Bijzondere categorieën | Ja | WMO, Jeugdzorg = gezondheidsgegevens |
| Internationale doorgifte | Nee | Overheid blijft doorgaans in EU |
| Verwerkingen | 100+ | Grote gemeente = veel verwerkingen |
| **Continuïteit** | | |
| BCP | Nee | Veel gemeenten hebben dit nog niet |
| Incident Response | Nee | Idem |
| Max downtime | Dag | Kritiek maar niet uren-kritisch |
| **Mensen** | | |
| Bewustwording | Ja | BIO vereist dit |
| Screening | Ja | Overheidsfunctie = VOG |
| Training | Jaarlijks | Minimumeis BIO |

### Technische aanpak

#### Optie A: Rule-based (geen AI, deterministisch) ✅ AANBEVOLEN

Een Python-dict met prefill-regels op basis van `org_type` + `sector` + `employee_count`. Geen LLM-call nodig voor voorspelbare overheidsorganisaties.

**Voordelen:** Snel, deterministisch, geen AI-afhankelijkheid, offline werkend.
**Nadelen:** Beperkt tot voorgedefinieerde combinaties.

#### Optie B: LLM-based (Ollama/Mistral)

Backend-endpoint dat een prompt stuurt naar de lokale LLM met de Identiteit-gegevens en een JSON-schema terugvraagt.

**Voordelen:** Flexibel, werkt voor onbekende combinaties.
**Nadelen:** Trager (~3-5s), vereist draaiende Ollama, kan hallucineren.

#### Optie C: Hybrid (rule-based + LLM fallback)

Rules voor bekende combinaties, LLM voor de rest.

### Gekozen aanpak: Optie A (rule-based)

Reden: de meeste IMS-gebruikers zijn overheidsorganisaties (gemeenten, waterschappen, provincies, ZBO's). De combinaties zijn voorspelbaar. LLM kan later als upgrade.

### Implementatie

**Backend: nieuw endpoint**

```
POST /api/v1/organization-profile/prefill
Body: { "org_type": "Gemeente", "sector": "Overheid", "employee_count": "500+", ... }
Response: { "has_dpo": true, "applicable_frameworks": "BIO, AVG", ... }
```

Nieuw bestand: `backend/app/api/v1/endpoints/org_prefill.py`

Bevat een `PREFILL_RULES`-dict met regels per org_type/sector-combinatie:

```python
PREFILL_RULES = {
    ("Gemeente", "Overheid"): {
        "applicable_frameworks": "BIO, AVG",
        "has_security_officer": True,
        "has_dpo": True,
        "governance_maturity": "Basis",
        "risk_appetite_availability": "Laag",
        # ...
    },
    ("Waterschap", "Overheid"): { ... },
    ("Zorginstelling", "Zorg"): { ... },
    # etc.
}
```

Fallback: als combinatie onbekend → lege response (gebruiker vult zelf in).

**Frontend: state + UI**

1. Na `save_step()` in stap 0 → roep `prefill_from_identity()` aan
2. State method roept het prefill-endpoint aan
3. Vult alleen **lege** velden — eerder ingevulde waarden worden NIET overschreven
4. Toon een toast/banner: *"Op basis van uw organisatieprofiel hebben we een voorzet gedaan. Controleer en pas aan waar nodig."*
5. Visuele indicator: prefilled velden krijgen een subtiele markering (bijv. lichtblauwe achtergrond of een klein ✨ icoon) zodat de gebruiker weet wat door AI is ingevuld

**Bestanden die wijzigen:**

| Bestand | Wijziging |
|---------|-----------|
| `backend/app/api/v1/endpoints/org_prefill.py` | **Nieuw** — prefill rules + endpoint |
| `backend/app/api/v1/api.py` | Router toevoegen |
| `frontend/ims/api/client.py` | Nieuw: `prefill_organization()` method |
| `frontend/ims/state/organization_profile.py` | Nieuw: `prefill_from_identity()` handler, `prefilled_fields: list` state var |
| `frontend/ims/pages/organization.py` | Banner na prefill, visuele markering prefilled velden |

---

## Volgorde van implementatie

1. **Tooltips** (wijziging 1) — puur frontend, geen risico
2. **Prefill-rules backend** — nieuw endpoint met deterministische regels
3. **Prefill frontend-integratie** — state + UI aanpassingen
4. **Prefill visuele feedback** — banner + markering van voorgestelde waarden

---

## Niet in scope

- LLM-based prefill (kan later als upgrade)
- Inline editing in profielweergave (apart verhaal)
- Wijzigingen aan het backend-model `OrganizationProfile`

# GRC-platform — Gebruik

> Voor CISO's, ISO's, TIMS-leden en informatiebeveiligingscoördinatoren die het platform inrichten of gebruiken.

---

## Eerste keer opstarten

Na installatie (zie README) bereik je het platform op `http://localhost:3000`.

1. Log in met het standaard beheerderaccount (`admin@example.com` / het wachtwoord uit je `.env`)
2. Maak direct een nieuw wachtwoord aan via **Profiel → Wachtwoord wijzigen**
3. Ga naar **Beheer → Organisaties** om je eigen organisatie aan te maken
4. Wijs een beheerder en TIMS-rollen toe via **Beheer → Gebruikers**

---

## IMS inrichten — de wizard

De kern van het platform is de inrichtingswizard: 22 stappen door 4 fasen. Je doorloopt dit **één keer per organisatie**, gevolgd door regulier onderhoud.

### De vier fasen

| Fase | Stappen | Wat je doet |
|------|---------|-------------|
| **1. Fundament** | 1–5 | Scope, beleid, rollen, bestuurlijk draagvlak |
| **2. Analyse** | 6–11 | Bedrijfsprocessen, assets, dreigingen, risicobeoordeling |
| **3. Maatregelen** | 12–17 | Controls selecteren, implementeren, koppelen aan normen |
| **4. Werking** | 18–22 | Monitoring, audits, incidenten, managementreview |

### Navigeren

- Elke stap heeft een eigen scherm met uitleg en invulvelden
- Je kunt terug naar vorige stappen om informatie bij te werken
- De voortgangsindicator bovenin toont waar je bent
- AI-ondersteuning (indien geconfigureerd) geeft contextuele hints per stap

---

## Dagelijks gebruik na inrichting

### Risicobeheer

- **GRC → Risico's**: overzicht van alle geregistreerde risico's
- Nieuw risico: klik **+ Risico** en vul dreigingsbron, asset, kans en impact in
- Elk risico krijgt automatisch een risicoscore en wordt gekoppeld aan de toepasselijke norm(en)

### Controls en maatregelen

- **GRC → Controls**: alle maatregelen gekoppeld aan normen (BIO, ISO 27001, etc.)
- Status per control: `niet van toepassing` / `gepland` / `geïmplementeerd` / `geverifieerd`
- Controls koppelen aan risico's: open een control en selecteer gekoppelde risico's

### Audits en assessments

- **GRC → Assessments**: plan een interne audit of zelfevaluatie
- Selecteer de scope (normen, controls, processen) en wijs een verantwoordelijke toe
- Bevindingen worden direct gekoppeld aan controls en risicoregistratie

### Bewijsbeheer (evidence)

- **GRC → Bewijs**: upload documenten, beleidsstukken of testresultaten
- Koppel bewijs aan een of meerdere controls
- Bewijs heeft een vervaldatum voor periodieke herbevestiging

### Incidenten

- **GRC → Incidenten**: registreer een beveiligingsincident of privacy-incident
- Vul de tijdlijn, betrokken assets, en getroffen maatregelen in
- Incidenten worden automatisch meegenomen in de PDCA-cyclus

---

## Rollen

| Rol | Wat je kunt |
|-----|-------------|
| **Admin** | Volledige toegang, gebruikersbeheer, tenantbeheer |
| **CISO** | Alle GRC-functies, rapportages, assessments aanmaken |
| **TIMS-lid** | Controls en risico's beheren, bewijs toevoegen |
| **Auditor** | Assessments uitvoeren, bevindingen registreren (geen bewerkrechten) |
| **Viewer** | Alleen-lezen toegang tot GRC-data van de eigen organisatie |

---

## Multi-organisatie

Het platform ondersteunt meerdere organisaties (tenants) in één installatie. Elke organisatie heeft een volledig afgeschermde dataruimte — Row Level Security op databaseniveau zorgt dat data nooit per ongeluk lekt tussen organisaties.

Beheerders van één organisatie kunnen de data van andere organisaties niet zien, ook niet als ze ingelogd zijn als platformbeheerder.

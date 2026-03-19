# IMS Handboek (concept) — Feedback Bas
*Opgesteld: 13 maart 2026*
*Bron: vergelijking handboek vs. CONTEXT.md (IMS-proces) en Totaalplaatje*

---

## Feedbackpunten

### 1. SIMS: CISO wordt toezichthouder
De CISO staat in het handboek als regulier lid van SIMS. Moet worden: **adviseur zonder beslisrecht**. De CISO is 3e lijn (onafhankelijk toezicht), niet 2e lijn. Past bij het Three Lines Model: toezichthouder beslist niet mee.

**Actie:** SIMS-samenstelling aanpassen. CISO als adviseur vermelden, niet als lid.

---

### 2. TIMS: FG, Interne Accountant en CISO eruit
Het handboek zet FG, Interne Accountant en CISO als leden in TIMS. Dat is onjuist — zij zijn 3e lijn en horen niet in een tactisch coördinerend gremium. Anders vervuilt de scheiding tussen toezicht en uitvoering.

**Actie:** FG, Interne Accountant en CISO verwijderen uit TIMS-samenstelling. Projectleider (Bas) toevoegen als voorzitter.

---

### 3. ISMS → IMS
Het handboek gebruikt op meerdere plekken "ISMS" waar "IMS" bedoeld wordt (o.a. §9.3, §10.1). Het gaat om het integrale managementsysteem, niet alleen informatiebeveiliging.

**Actie:** Global replace "ISMS" → "IMS", tenzij het specifiek over het ISMS-domein (informatiebeveiliging) gaat.

---

### 4. Splits handboek in blueprint en Leiden-versie
Het handboek is nu een mix van generieke structuur (blueprint) en Leiden-specifieke invulling. Dit maakt het rommelig en onbruikbaar als template voor andere gemeenten.

**Actie:** Maak twee versies:
- **Blueprint**: generiek skelet met placeholders. Wordt het template dat IMS-proces agents gebruiken om een gemeente-specifiek handboek te genereren.
- **Leiden-versie**: ingevuld met Leidse context, namen, stakeholders, risicobereidheid etc.

De huidige placeholders (`<tekst> van Luuk`, `Visie: <OMSCHRIJVING>`, lege bijlage 1, lege rapportagetabel) worden in de blueprint bewuste placeholders. In de Leiden-versie worden ze ingevuld. Het VOORSTEL-blok (Visie/Missie/Strategie) vervangt de placeholder in de Leiden-versie.

---

### 5. Privacy-aantallen: overal 154 controls
Inconsistente aantallen voor het privacy-domein in de documentatie. Het juiste getal is **154 controls**.

**Actie:** Overal bijwerken naar `AVG · 154 controls`:
- Totaalplaatje §1 tabel (`~40 kernverplichtingen` → `154 controls`)
- Olifant-prompt (`AVG · 40 verplichtingen` → `AVG · 154 controls`)
- Handboek indien van toepassing

---

### 6. Lege/placeholder secties
Valt onder punt 4. In de blueprint worden dit bewuste placeholders, in de Leiden-versie worden ze ingevuld.

---

### 7. Zes ontbrekende onderwerpen toevoegen
Het handboek mist zes onderwerpen die in CONTEXT.md als verplichte (V) outputs staan en door ISO worden vereist. Passend bij het diepgangniveau van het handboek: **korte alinea** (wat, wie, wanneer, eigenaar) met **verwijzing naar apart document** voor de uitwerking.

| Onderwerp | ISO-grondslag | Toevoegen als |
|---|---|---|
| Privacy by Design procedure | ISO 27701 7.4/8.4, AVG art. 25 | Alinea + verwijzing naar PbD-procedure |
| PII-doorgifte (transfers) | ISO 27701 7.5/8.5 | Alinea + verwijzing naar doorgifte-register |
| BC-oefeningen | ISO 22301 8.5 | Alinea + verwijzing naar oefenprogramma |
| BIA (uitgewerkt) | ISO 22301 8.2.2 | Bestaande tekst kan zo blijven (verwijst al naar apart doc) |
| Incidentmanagement | ISO A.5.24-28, AVG 33/34 | Alinea + verwijzing naar incidentprocedure |
| Risicomethodiek (schalen, criteria) | ISO 6.1.2 | **Uitwerken in bijlage 3** (niet apart document) |

**Uitzondering:** De risicobeoordelingsmethodiek (impactschalen, kansschalen, acceptatiecriteria) hoort wél volledig in het handboek zelf (bijlage 3). Dit is het fundament waar alle risicoanalyses op draaien.

---

### 8. Risicobereidheid: groen expliciet benoemen
Het handboek beschrijft drie kleurniveaus (rood, oranje, geel) maar mist groen. De rest van de documentatie (Totaalplaatje, olifant-prompt, CONTEXT.md) gebruikt vier niveaus.

**Actie:** Groen als vierde niveau toevoegen:
- **Groen**: discipline-eigenaar of risico-eigenaar monitort. Mag onderbouwd accepteren. TIMS kan bepalen dat zij niet akkoord gaan.

Dit maakt de escalatieladder compleet en consistent:
🟢 Groen → discipline-eigenaar
🟡 Geel → TIMS
🟠 Oranje → SIMS
🔴 Rood → Directieteam

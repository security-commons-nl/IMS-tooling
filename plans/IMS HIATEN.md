Hieronder staat een **concreet, app-intern bouw- en borgingsplan** voor **elk van de 7 IMS-hiaten**.
Niet als visie, maar als **wat je toevoegt aan déze applicatie**: objecten, schermen, regels en governance-werking.

Ik ga steeds langs dezelfde structuur:

* **Wat moet er komen (functioneel)**
* **Hoe borg je dit in de app (hard, afdwingbaar)**
* **Wat levert dit bestuurlijk op**

---

# 1. Besluitlog (DT-besluiten) — *grootste hiaat*

## Wat moet er komen

Een **Besluit** als zelfstandig object.

**Besluittypes**

* Restrisico-acceptatie
* Prioritering (volgorde maatregelen)
* Afwijking (bewust niet voldoen)

**Kernvelden**

* Besluit-ID
* Type besluit
* Gekoppeld(e) risico(’s)
* Besluittekst
* Besluitnemer (DT)
* Datum
* Geldig tot / herijkdatum
* Status (actief / verlopen)

---

## Hoe borg je dit in de app

* **Nieuw menu-item**: `Besluiten`
* **Hard rule**:

  * Risico met score ≥ X → **geen status “afgehandeld” zonder besluit**
* **Automatische signalering**:

  * Verlopen besluit → risico springt terug naar *“besluit vereist”*
* **DT-rol only**:

  * Alleen DT-rol kan besluiten vaststellen

---

## Bestuurlijke waarde

* Geen impliciete risicoacceptatie meer
* Audit-proof antwoord op: *“wie heeft dit besloten?”*
* ACT-fase wordt expliciet

---

# 2. Bestuurlijke scope-objecten (niet alleen lijstjes)

## Wat moet er komen

Een **IMS-Scope** als document/object, niet alleen als filter.

**Scopevelden**

* Scope-naam
* Beschrijving
* In scope / out of scope
* Motivatie
* Geldigheid (jaar)
* Vastgesteld door (DT)
* Datum vaststelling

---

## Hoe borg je dit in de app

* Scope = **verplicht veld** bij:

  * risico
  * control
  * audit
* **Scope-status**:

  * concept / vastgesteld / verlopen
* **Blokkade**:

  * Geen nieuwe risico’s in een verlopen scope
* **Exportfunctie**:

  * “IMS-scopeverklaring” (PDF/Word)

---

## Bestuurlijke waarde

* Heldere afbakening
* Antwoord op *“waarom valt dit erbuiten?”*
* Essentieel voor audits en bestuur

---

# 3. Risicokader & risicobereidheid

## Wat moet er komen

Een **Risicokader-object** per IMS of per scope.

**Inhoud**

* Impactdefinities (CIA / privacy / continuïteit)
* Kansdefinities
* Risicotolerantie
* Beslisregels (wanneer DT-besluit vereist)

---

## Hoe borg je dit in de app

* **Centraal risicokader-scherm**
* Risicoscore = **altijd afgeleid**, niet vrij invoerbaar
* **Tooltip / hover**:

  * Wat betekent “Hoog”?
* **Versiebeheer**:

  * Oud kader blijft zichtbaar bij oude risico’s

---

## Bestuurlijke waarde

* Scores krijgen betekenis
* Vergelijkbaarheid tussen risico’s
* DT stuurt op **kader**, niet op onderbuik

---

# 4. Verplichte behandelstrategie per risico

## Wat moet er komen

Expliciete **Behandelstrategie** als verplicht veld.

**Keuzes**

* Vermijden
* Reduceren
* Overdragen
* Accepteren

---

## Hoe borg je dit in de app

* Risico kan pas naar “actief” als strategie is gekozen
* **Acceptatie → automatisch besluit vereist**
* **Reducerend**:

  * Minimaal één control verplicht
* **Overdragen**:

  * Leverancier / verzekering verplicht veld

---

## Bestuurlijke waarde

* Duidelijkheid over intentie
* Geen “we doen iets” zonder richting
* Koppeling tussen risico en maatregel

---

# 5. In-control oordeel per scope / domein

## Wat moet er komen

Een **In-Control Status** per scope.

**Statussen**

* In control
* Beperkt in control
* Niet in control

Met onderbouwing:

* open risico’s
* ontbrekende controls
* auditbevindingen

---

## Hoe borg je dit in de app

* **Automatisch berekend**, maar:

  * Alleen DT kan status vaststellen
* **In-control dashboard**:

  * per scope
  * per domein (ISMS / PIMS / BCMS)
* **Verplichte motivatie** bij “in control”

---

## Bestuurlijke waarde

* Heldere uitspraak mogelijk
* Geen vage dashboards
* Direct inzetbaar voor P&C en verantwoording

---

# 6. Traceerbaarheid beleid → risico → control

## Wat moet er komen

**Beleid als normatief object**, niet alleen document.

**Structuur**

* Beleid

  * → beleidsprincipe

    * → risico

      * → control

---

## Hoe borg je dit in de app

* Beleidsmodule uitbreiden:

  * beleidsregel-ID
* Risico **moet** aan minimaal één beleidsregel hangen
* Control **erft** beleidskoppeling
* **Trace view**:

  * “waarom bestaat deze control?”

---

## Bestuurlijke waarde

* Aantoonbare normwerking
* Geen losstaande maatregelen
* Sterk richting FG en audit

---

# 7. ACT-feedbackloop (sluiten van de PDCA)

## Wat moet er komen

Een **verplichte opvolgcyclus** na toetsing.

**Logica**

* Auditbevinding → actie
* Actie → herbeoordeling risico
* Herbeoordeling → nieuw besluit (indien nodig)

---

## Hoe borg je dit in de app

* Bevinding kan niet “afgesloten” zonder:

  * actie
  * herbeoordeling
* Herbeoordeling verandert:

  * risicoscore
  * behandelstrategie
* **Automatische signalering**:

  * ACT open > X dagen → DT-dashboard rood

---

## Bestuurlijke waarde

* Geen open eindjes
* PDCA sluit aantoonbaar
* Continu verbeteren wordt zichtbaar

---

# Overzicht: hoe dit samenkomt

| IMS-element | App-borging                            |
| ----------- | -------------------------------------- |
| PLAN        | Scope + Risicokader + Beleid           |
| DO          | Risico + Behandelstrategie + Controls  |
| CHECK       | Audits + bewijs + in-control indicator |
| ACT         | Besluitlog + herbeoordeling            |

---

## Minimale volgorde van bouwen (advies)

1. Besluitlog
2. Scope-objecten
3. Risicokader
4. Behandelstrategie
5. In-control status
6. Beleid-trace
7. ACT-feedbackloop

Zo groeit je tool **van GRC naar IMS**.
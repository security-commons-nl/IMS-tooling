Hier is **uitwerking van punt 1 en 2**, concreet en implementatiegericht, op jouw bestaande model.

---

## 1. Hard SoD / 4-eyes model (governance die je niet kunt omzeilen)

### Doel

Voorkomen dat **één persoon** risico’s accepteert, beleid publiceert of compliance “groen kleurt” zonder onafhankelijke toetsing. Dit is geen UI-feature, maar **platformgedrag**.

### A. Welke acties vallen onder verplicht 4-eyes

Maak dit **niet configureerbaar per gebruiker**, alleen per tenant:

| Actie                                 | Waarom                   |
| ------------------------------------- | ------------------------ |
| Risicoacceptatie (≥ drempel)          | Bestuurlijk restrisico   |
| SoA-status → *Implemented / Approved* | Compliance-claim         |
| Policy → *Publish*                    | Normatieve werking       |
| Exception/Waiver → *Approved*         | Bewuste afwijking        |
| Control effectiveness > X%            | Beïnvloedt residual risk |
| Shared control adequacy = true        | Afhankelijkheid derden   |

---

### B. SoD-regels (hard, afdwingbaar)

#### 1. Rolscheiding

Introduceer een **DecisionRoleMatrix** (config per tenant):

| Actie          | Initiator | Reviewer              | Approver               |
| -------------- | --------- | --------------------- | ---------------------- |
| Risk Accept    | Eigenaar  | Coordinator (2e lijn) | Toezichthouder / DT    |
| Policy Publish | Auteur    | Coordinator           | Eigenaar               |
| SoA Approve    | Eigenaar  | Coordinator           | Toezichthouder         |
| Exception      | Eigenaar  | Coordinator           | Eigenaar *ander scope* |

**Regel:**

> *Initiator ≠ Reviewer ≠ Approver*

Technisch: afdwingen in API vóór state-transition.

---

#### 2. Scope-onafhankelijkheid

Extra harde regel:

> Reviewer/Approver mag **niet primair eigenaar** zijn van dezelfde scope.

Dit voorkomt “ik keur mijn eigen domein goed”.

---

### C. Implementatie (technisch)

#### 1. Nieuw entiteit: `ApprovalChain`

```text
ApprovalChain
- entity_type
- entity_id
- action_type
- initiator_user_id
- reviewer_user_id
- approver_user_id
- status (Pending / Reviewed / Approved / Rejected)
- decision_rationale
- timestamps
```

#### 2. Workflow-integratie

* Elke kritieke transition krijgt `requires_approval=true`
* Workflow engine valideert:

  * rol
  * scope
  * SoD-regels
* AI mag **samenvatten**, nooit goedkeuren

#### 3. Audit trail

Elke afwijzing of goedkeuring:

* verplicht motiveringsveld
* zichtbaar in management review
* exporteerbaar per auditperiode

---

### D. UX-regel (belangrijk)

Maak dit **frictievol maar duidelijk**:

* “Je kunt dit niet zelf goedkeuren.”
* Toon *wie* moet goedkeuren en *waarom*.

---

## 2. Evidence lifecycle (van losse uploads naar bewijsdiscipline)

### Doel

Auditors willen niet “een document”, maar antwoord op:

> *Is deze control aantoonbaar, actueel en effectief?*

Daarvoor moet evidence **gestructureerd, herhaalbaar en tijdgebonden** zijn.

---

### A. Evidence als first-class object

Breid `Evidence` uit met **normatieve betekenis**:

```text
Evidence
- evidence_type (Document, Log, Config, Screenshot, Report)
- linked_control_id
- linked_requirement_id
- validity_start
- validity_end
- freshness_policy (days)
- source_type (Manual, Integration, AI, External)
- verification_status (Unverified, Verified, Rejected)
- verified_by
- verification_date
- confidence_score
```

---

### B. Evidence-eisen per control

Nieuwe entiteit: `ControlEvidenceRequirement`

```text
ControlEvidenceRequirement
- control_id
- required_evidence_type
- frequency (monthly / quarterly / annually)
- minimum_freshness_days
- mandatory (true/false)
```

Voorbeeld:

* Control: *Patchmanagement*

  * Logbestand, elke maand, max 30 dagen oud
  * Rapport, elk kwartaal

---

### C. Evidence lifecycle (proces)

#### 1. Requirement → Control → Evidence

* SoA bepaalt **welke controls actief zijn**
* Controls definiëren **welk bewijs nodig is**
* Platform bewaakt of bewijs bestaat én actueel is

#### 2. Statusmodel

| Status         | Betekenis                   |
| -------------- | --------------------------- |
| Missing        | Geen bewijs                 |
| Expired        | Verlopen                    |
| Pending Review | Nieuw, nog niet getoetst    |
| Verified       | Goedgekeurd                 |
| Rejected       | Afgekeurd (verplicht actie) |

Status beïnvloedt:

* Control effectiveness
* Residual risk
* In Control-dashboard

---

### D. Evidence freshness engine

Automatische checks:

* `now > validity_end` → **Expired**
* `now > last_upload + freshness_policy` → waarschuwing
* Missing evidence → finding genereren

API:

```
GET /controls/{id}/evidence-status
```

---

### E. AI-ondersteuning (realistisch, geen magie)

AI mag:

* Evidence **samenvatten**
* Control-vraag beantwoorden: *“Is dit logisch bewijs?”*
* Flaggen: Partial / Weak / Mismatch

AI mag **niet**:

* Evidence goedkeuren
* Status “Verified” zetten

AI-output → Reviewer-beslissing.

---

### F. Audit-proof output

Per scope + periode:

* Controls
* Vereiste evidence
* Laatste verificatiestatus
* Afwijkingen + acties

= **Audit pack** zonder extra handwerk.

---

## Samengevat in 1 zin

1️⃣ Je SoD-model maakt governance afdwingbaar in plaats van adviserend.
2️⃣ Je evidence lifecycle verandert losse uploads in aantoonbare, herhaalbare compliance.

Als je wilt, kan ik dit volgende keer:

* vertalen naar **datamodel + API-endpoints**, of
* prioriteren naar **“wat moet er af voor MVP+”**.

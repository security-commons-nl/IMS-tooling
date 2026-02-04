# Werkwijze Beheer en Ontwikkeling

Dit document beschrijft de werkwijze voor beheer en ontwikkeling van het IMS project.

## Development Lifecycle

Elke wijziging doorloopt de volgende fasen voordat implementatie start:

### 1. Backlog Management

**Regel:** Geen implementatie zonder backlog item.

- Elk verzoek, bug, of idee wordt eerst als item in de backlog opgenomen
- Items bevatten minimaal: titel, beschrijving, acceptatiecriteria
- Backlog is de single source of truth voor gepland werk

### 2. Prioritering

**Regel:** Alleen geprioriteerde items komen in aanmerking voor planning.

Prioritering gebeurt op basis van:
- **Business value** - wat levert het op voor de organisatie?
- **Urgentie** - zijn er deadlines of afhankelijkheden?
- **Risico** - wat is het risico van niet-implementeren?
- **Effort** - hoeveel werk kost het (t-shirt sizing: S/M/L/XL)?

Prioriteitslevels:
- 🔴 **Critical** - moet deze sprint
- 🟠 **High** - volgende sprint
- 🟡 **Medium** - binnen 3 sprints
- 🟢 **Low** - nice to have

### 3. Planning

**Regel:** Geprioriteerde items worden pas geïmplementeerd na expliciete planning.

Planning omvat:
- Toewijzing aan sprint/iteratie
- Definition of Done vaststellen
- Afhankelijkheden identificeren
- Technische aanpak bepalen (bij complexe items)

### 4. Implementatie

**Regel:** Implementatie start pas als item bovenaan de backlog staat, geprioriteerd én gepland is.

Implementatie workflow:
1. Item naar "In Progress" verplaatsen
2. Code/documentatie schrijven
3. Elke wijziging committen en pushen (zie Versiebeheer)
4. Pull request maken (bij feature branches)
5. Code review (indien van toepassing)

### 5. Testen

**Regel:** Geen deployment zonder testen. Testtype afhankelijk van wijziging.

Zie sectie "Test Strategie" voor details.

---

## Test Strategie

### Automatische Testen

| Type | Wanneer | Tool |
|------|---------|------|
| **Unit tests** | Elke code wijziging | pytest |
| **Integration tests** | API wijzigingen | pytest + httpx |
| **E2E tests** | UI wijzigingen | Playwright/Cypress |
| **Linting** | Elke commit | ruff, eslint |
| **Type checking** | Elke commit | mypy, pyright |

**CI/CD Pipeline:**
- Automatische tests draaien bij elke push
- Merge naar main alleen mogelijk als tests slagen
- Coverage rapportage bij pull requests

### Menselijke Testen

| Type | Wanneer | Door wie |
|------|---------|----------|
| **Functionele test** | Nieuwe features | Product owner / tester |
| **Usability test** | UI wijzigingen | Eindgebruiker |
| **Acceptance test** | Voor release | Stakeholder |
| **Exploratory test** | Complexe features | Tester |

**Acceptatiecriteria:**
- Functionele tests doorlopen acceptatiecriteria uit backlog item
- Afwijkingen worden als bug terug in backlog geplaatst

### Security Testen

**Regel:** Security tests zijn verplicht bij infrastructuur- of security-gerelateerde wijzigingen.

**Triggers voor security testing:**
- Wijzigingen aan authenticatie/autorisatie
- Nieuwe API endpoints
- Database schema wijzigingen
- Dependency updates
- Infrastructure as Code wijzigingen
- Netwerk configuratie aanpassingen

**Security test types:**

| Type | Frequentie | Tool |
|------|------------|------|
| **Dependency scanning** | Elke build | pip-audit, npm audit |
| **SAST (Static Analysis)** | Elke commit | bandit, semgrep |
| **Secret scanning** | Elke commit | gitleaks, trufflehog |
| **DAST (Dynamic Analysis)** | Voor release | OWASP ZAP |
| **Penetration test** | Jaarlijks / major release | Externe partij |

**OWASP Top 10 checklist:**
- [ ] Injection (SQL, Command, etc.)
- [ ] Broken Authentication
- [ ] Sensitive Data Exposure
- [ ] XML External Entities (XXE)
- [ ] Broken Access Control
- [ ] Security Misconfiguration
- [ ] Cross-Site Scripting (XSS)
- [ ] Insecure Deserialization
- [ ] Using Components with Known Vulnerabilities
- [ ] Insufficient Logging & Monitoring

---

## Versiebeheer Principes

### Elke wijziging wordt gecommit

**Regel:** Elke wijziging aan code of documentatie wordt direct gecommit en gepusht naar de remote repository.

**Werkwijze:**
1. Wijziging maken (Edit/Write)
2. `git add` - gewijzigde bestanden stagen
3. `git commit` - met beschrijvende commit message
4. `git push` - direct naar remote pushen

**Rationale:**
- Volledige traceerbaarheid van alle wijzigingen
- Geen verlies van werk bij lokale problemen
- Directe synchronisatie met remote repository
- Kleine, atomaire commits zijn makkelijker te reviewen en te reverten

### Commit Message Conventies

Gebruik conventionele commit messages:
- `feat:` - nieuwe functionaliteit
- `fix:` - bugfix
- `docs:` - documentatie wijzigingen
- `refactor:` - code refactoring zonder functionele wijziging
- `style:` - formatting, whitespace
- `test:` - toevoegen of aanpassen van tests
- `chore:` - overige taken (dependencies, config)

### Branch Strategie

- `main` - stabiele hoofdbranch
- Feature branches voor grotere wijzigingen (optioneel)

## AI-Assisted Development

Bij gebruik van Claude Code (of vergelijkbare AI tools):
- AI commit en pusht elke wijziging automatisch
- Gebruiker behoudt controle via code review op remote
- Kleine commits maken rollback eenvoudig indien nodig

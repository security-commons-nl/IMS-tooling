"""Add uitleg and voorbeeld_content to ims_steps

Revision ID: 008
Revises: 007
Create Date: 2026-03-30
"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ims_steps", sa.Column("uitleg", sa.Text(), nullable=True))
    op.add_column("ims_steps", sa.Column("voorbeeld_content", JSONB, nullable=True))

    # ── Uitleg teksten voor alle 22 stappen ────────────────────────────
    uitleg_data = [
        # Fase 0
        ("1", "In deze stap vraagt u het bestuur om toestemming om het IMS op te zetten. U krijgt een besluitmemo dat u kunt voorleggen aan het college of de directie. Zonder deze toestemming kan uw team geen beslissingen nemen of budget inzetten."),
        ("2a", "U brengt in kaart in welke context uw gemeente opereert: wie zijn de belanghebbenden, welke wet- en regelgeving is van toepassing, en welke rol speelt uw gemeente bij het verwerken van persoonsgegevens? Dit is de basis voor alle volgende stappen."),
        ("2b", "U bepaalt op welke onderdelen van uw organisatie het IMS van toepassing is. Welke afdelingen, domeinen en locaties vallen binnen scope? Dit wordt een formeel besluit."),
        ("3a", "U werkt uit hoe het IMS wordt bestuurd: wie zit in welk overleg, wie rapporteert aan wie, en wat is het beleid. Dit is nog een voorstel -- het besluit volgt in de volgende stap."),
        ("3b", "Het strategisch gremium keurt het governance-voorstel goed. Na dit besluit is de structuur officieel en kan iedereen erop worden aangesproken."),
        ("4", "U voert een nulmeting uit: waar staat uw gemeente nu ten opzichte van de norm? Per domein (informatiebeveiliging, privacy, bedrijfscontinuiteit) wordt gekeken wat er al is en wat er mist."),
        ("5", "U inventariseert welke registers er al zijn, brengt de eerste risico's in kaart, en stelt een methodiek vast voor hoe u risico's beoordeelt. Dit hoeft niet perfect te zijn -- een werkbare eerste versie volstaat."),
        ("6", "U stelt vast welke normen van toepassing zijn en selecteert een minimale set maatregelen (controls) op basis van de belangrijkste risico's. Dit is de randvoorwaarde voordat lijnmanagement aan de slag kan."),
        # Fase 1
        ("7", "Lijnmanagement wordt voorbereid op hun rol in het IMS. Ze leren wat er van hen verwacht wordt en in welke taal het systeem communiceert."),
        ("8", "U legt vast welke processen welke systemen gebruiken en welke persoonsgegevens daarin zitten. Dit register is nodig voor de risicoanalyse."),
        ("9", "Lijnmanagement voert de daadwerkelijke risicoanalyse uit per afdeling of proces. De methodiek en registers zijn beschikbaar -- nu is het aan de lijn."),
        ("10", "Per risico wordt bepaald: accepteren, mitigeren, overdragen of vermijden. Controls worden toegewezen aan eigenaren met een implementatieplan."),
        ("11", "U stelt vast welke ISO-controls van toepassing zijn en waarom. Dit document (SoA) is vereist voor certificering en bewijst een weloverwogen keuze."),
        ("12", "U richt de monitoring in: KPI's, rapportagelijnen en dashboards. Zonder dit kan het strategisch gremium niet sturen op resultaten."),
        # Fase 2
        ("13", "U plant en voert interne audits uit om te toetsen of de maatregelen daadwerkelijk werken. De resultaten zijn input voor de management review."),
        ("14", "Het strategisch gremium beoordeelt de auditresultaten, risicostatus en KPI's. Dit is het moment waarop de verbetercyclus sluit op strategisch niveau."),
        ("15", "Afwijkingen en incidenten worden geregistreerd, geanalyseerd en opgevolgd. Deze stap is doorlopend -- niet gebonden aan een vast moment."),
        ("16", "U verzamelt bewijs dat de maatregelen werken: per control, met continue monitoring. Zonder bewijs is een audit niet te doorstaan."),
        ("17", "De PDCA-cyclus wordt verankerd in de jaarplanning. Risico's worden herbeoordeeld en de volgende cyclus wordt gepland."),
        # Fase 3
        ("18", "U bereidt de organisatie voor op externe certificering. Een pre-audit brengt resterende gaps in beeld."),
        ("19", "Met voldoende historische data kunt u trends herkennen en proactief risico's voorspellen. Rapportages worden geautomatiseerd."),
        ("20", "U koppelt het IMS aan systemen van ketenpartners en leveranciers voor gestructureerde data-uitwisseling."),
        ("21", "U optimaliseert het normenkader door cross-mapping: een maatregel dekt meerdere normeisen tegelijk. Dit elimineert dubbel werk."),
        ("22", "Meerdere gemeenten vergelijken hun voortgang en delen best practices. Dit versnelt volwassenheid in de regio."),
    ]

    for number, uitleg in uitleg_data:
        op.execute(sa.text(
            "UPDATE ims_steps SET uitleg = :uitleg WHERE number = :number"
        ).bindparams(number=number, uitleg=uitleg))

    # ── Voorbeeld content voor Fase 0 stappen ─────────────────────────
    voorbeeld_data = {
        "1": {
            "title": "Voorbeeld: Besluitmemo IMS",
            "sections": [
                {"title": "Aanleiding", "content": "De gemeente wil haar informatiebeveiliging, privacy en bedrijfscontinuiteit structureel borgen conform BIO 2.0 en ISO 27001. Recente incidenten bij andere gemeenten onderstrepen de urgentie."},
                {"title": "Ambitieniveau", "content": "Fase 1: compliance met BIO 2.0. Op termijn (2028): certificering ISO 27001."},
                {"title": "Benodigde middelen", "content": "0,5 fte IMS-coordinator, licentiekosten IMS-tooling, budget voor externe audit in jaar 2. Discipline-eigenaren leveren elk 0,2 fte."},
                {"title": "Besluit", "content": "Het college besluit:\n1. Een Integrated Management System (IMS) in te richten voor informatiebeveiliging (ISMS), privacy (PIMS) en bedrijfscontinuiteit (BCMS).\n2. Het tactisch gremium mandaat te geven voor de inrichting.\n3. De genoemde middelen beschikbaar te stellen."},
            ],
        },
        "2a": {
            "title": "Voorbeeld: Organisatiecontext",
            "sections": [
                {"title": "Interne context", "content": "De gemeente heeft 450 medewerkers, 3 directies, en werkt met 120 applicaties. Er loopt een digitaliserings-programma. Capaciteit voor informatiebeveiliging is beperkt (1,5 fte)."},
                {"title": "Externe context", "content": "De gemeente verwerkt burgergegevens (BRP, WMO, Jeugdzorg), werkt samen in een gemeenschappelijke regeling met 4 buurgemeenten, en is aangesloten op Suwinet en DigiD."},
                {"title": "Stakeholders", "content": "Intern: college, directie, OR, afdelingshoofden. Extern: AP (toezichthouder privacy), ADR (BIO-toezicht), inwoners, ketenpartners."},
                {"title": "PII-rol", "content": "De gemeente is verwerkingsverantwoordelijke voor burgergegevens en personeelsgegevens. Voor Suwinet is de gemeente verwerker namens UWV/SVB."},
            ],
        },
        "2b": {
            "title": "Voorbeeld: Scopebesluit",
            "sections": [
                {"title": "Domeinen", "content": "Het IMS is van toepassing op: ISMS (informatiebeveiliging), PIMS (privacy) en BCMS (bedrijfscontinuiteit)."},
                {"title": "Organisatieonderdelen", "content": "Alle directies en afdelingen vallen binnen scope. De gemeenschappelijke regeling valt buiten scope maar wordt als externe partij behandeld."},
                {"title": "Uitsluitingen", "content": "Geen uitsluitingen. De raadsgriffie wordt meegenomen als informatiegebruiker, niet als proceseigenaar."},
            ],
        },
        "3a": {
            "title": "Voorbeeld: Governance-voorstel",
            "sections": [
                {"title": "Strategisch gremium", "content": "Samenstelling: gemeentesecretaris (voorzitter), directeur bedrijfsvoering, concerncontroller. Frequentie: kwartaal, 1,5 uur. Rol: strategische besluiten, budget, escalatie."},
                {"title": "Tactisch gremium", "content": "Samenstelling: IMS-coordinator (voorzitter), CISO, FG, BCM-manager. Frequentie: maandelijks, 2 uur. Rol: coordinatie, voortgang, inhoudelijke afstemming."},
                {"title": "Beleidsdoelstellingen", "content": "1. Voldoen aan BIO 2.0 binnen 12 maanden.\n2. Privacy-volwassenheid naar niveau 3 binnen 18 maanden.\n3. Bedrijfscontinuiteitsplannen operationeel voor kritische processen."},
            ],
        },
        "4": {
            "title": "Voorbeeld: Gap-analyse nulmeting",
            "sections": [
                {"title": "ISMS", "content": "Huidige score: 2,1 / 5. Toegangsbeheer is informeel geregeld. Geen classificatiebeleid. Patchmanagement ad hoc. Sterke punten: firewalls en antivirussoftware actueel."},
                {"title": "PIMS", "content": "Huidige score: 2,4 / 5. Register van verwerkingen bestaat maar is niet compleet. Geen DPIA-procedure. Datalekprocedure aanwezig maar niet getest."},
                {"title": "BCMS", "content": "Huidige score: 1,8 / 5. Geen BIA uitgevoerd. Kritische processen niet formeel geidentificeerd. Geen continuiteitsplannen."},
            ],
        },
        "5": {
            "title": "Voorbeeld: Registers en risicobeeld",
            "sections": [
                {"title": "Beschikbare registers", "content": "Applicatieregister (CMDB): aanwezig, 80% compleet. Register van verwerkingen: aanwezig, 60% compleet. Leveranciersregister: niet aanwezig. Lijst kritische processen: niet formeel vastgesteld."},
                {"title": "Top-5 risico's", "content": "1. Ransomware-aanval op gemeentelijk netwerk (kans: hoog, impact: zeer hoog)\n2. Onbevoegde toegang tot BRP-gegevens (kans: midden, impact: zeer hoog)\n3. Uitval MSI/MSO (kans: midden, impact: hoog)\n4. Datalek via email (kans: hoog, impact: midden)\n5. Leverancier-afhankelijkheid ICT (kans: midden, impact: hoog)"},
                {"title": "Methodiek", "content": "Risicobeoordeling op basis van kans (1-5) x impact (1-5). Acceptatieniveaus: groen (1-4), geel (5-9), oranje (10-14), rood (15-25). Rood vereist escalatie naar strategisch gremium."},
            ],
        },
        "6": {
            "title": "Voorbeeld: Normenkader en kerncontrols",
            "sections": [
                {"title": "Normenkader", "content": "Leidend: BIO 2.0 (verplicht voor gemeenten). Aanvullend: ISO 27001:2022 (certificeringsambitie), ISO 27701:2019 (privacy-extensie), ISO 22301:2019 (BCM)."},
                {"title": "Kerncontrols (top-10)", "content": "1. Toegangsbeheer en autorisatiebeheer (BIO 9.1)\n2. Patchmanagement en kwetsbaarheidsbeheer (BIO 12.6)\n3. Back-up en herstel (BIO 12.3)\n4. Incidentmanagement (BIO 16.1)\n5. Awareness-programma (BIO 7.2)\n6. Classificatie van informatie (BIO 8.2)\n7. Leveranciersbeheer (BIO 15.1)\n8. DPIA-procedure (AVG 35)\n9. Register van verwerkingen (AVG 30)\n10. Continuiteitsplannen kritische processen (ISO 22301 8.4)"},
            ],
        },
    }

    for number, content in voorbeeld_data.items():
        op.execute(sa.text(
            "UPDATE ims_steps SET voorbeeld_content = cast(:content as jsonb) WHERE number = :number"
        ).bindparams(number=number, content=json.dumps(content, ensure_ascii=False)))


def downgrade() -> None:
    op.drop_column("ims_steps", "voorbeeld_content")
    op.drop_column("ims_steps", "uitleg")

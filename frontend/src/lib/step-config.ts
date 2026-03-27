export interface StepConfig {
  stepNumber: string;
  title: string;
  description: string;
  outputs: string[];
}

export const STEP_CONFIGS: Record<string, StepConfig> = {
  '1': {
    stepNumber: '1',
    title: 'Bestuurlijk commitment',
    description:
      'Zonder formeel mandaat van het bestuur heeft het TIMS geen autoriteit om besluiten te nemen of middelen in te zetten. Dit is de juridische en bestuurlijke basis voor alles wat volgt.',
    outputs: ['Besluitmemo', 'Besluitlog #001'],
  },
  '2a': {
    stepNumber: '2a',
    title: 'Organisatiecontext vaststellen',
    description:
      'De scope, de stakeholders en de PII-rol van de gemeente moeten bekend zijn voordat er iets wordt ingericht. Zonder context kiest iedereen zijn eigen referentiekader.',
    outputs: ['Organisatiecontextdocument', 'Stakeholderregister', 'PII-rol'],
  },
  '2b': {
    stepNumber: '2b',
    title: 'Scope bepalen',
    description:
      'De scope bepaalt op welke organisatieonderdelen en domeinen het IMS van toepassing is. Zonder vastgestelde scope kun je geen gap-analyse uitvoeren — je weet niet wat je moet meten.',
    outputs: ['Formeel scopebesluit'],
  },
  '3a': {
    stepNumber: '3a',
    title: 'Governance- en beleidsvoorstel opstellen',
    description:
      'Nu de context en scope bekend zijn, kan het TIMS uitwerken hoe het IMS wordt bestuurd: wie zit waar, wie rapporteert aan wie, wat is het beleid. Dit is het ontwerp — nog geen besluit.',
    outputs: [
      'Concept governance-document',
      'Concept IMS-beleid',
      'Communicatiematrix',
    ],
  },
  '3b': {
    stepNumber: '3b',
    title: 'Governance en beleid vaststellen',
    description:
      'Het SIMS stelt het governance-voorstel van het TIMS formeel vast. Pas na dit besluit is de structuur gezaghebbend en kan lijnmanagement straks worden aangesproken op hun rol.',
    outputs: ['Formeel governance-besluit', 'IMS-beleid (definitief)', 'Besluitlog'],
  },
  '4': {
    stepNumber: '4',
    title: 'Gap-analyse',
    description:
      'Met governance vastgesteld en scope duidelijk kan de nulmeting beginnen: waar staan we nu ten opzichte van de norm? Deze meting is de basis voor alles wat daarna geprioriteerd wordt.',
    outputs: ['Nulmeting per domein', 'Volwassenheidsprofiel v1'],
  },
  '5': {
    stepNumber: '5',
    title: 'Registers & risicobeoordeling',
    description:
      'De gap-analyse laat zien wat ontbreekt. Nu worden de basisregisters opgebouwd en de eerste risico\'s in kaart gebracht — zodat stap 6 controls kan selecteren op basis van echte risico\'s, niet op aannames.',
    outputs: [
      'Registerinventarisatie',
      'Eerste risicobeeld',
      'Risicobeoordelingsmethodiek',
    ],
  },
  '6': {
    stepNumber: '6',
    title: 'Normenkader & kerncontrols',
    description:
      'Het normenkader en de minimale werkset controls zijn de randvoorwaarde voor Fase 1. Zonder dit weet lijnmanagement niet op basis van welke maatregelen ze moeten werken.',
    outputs: ['Normenkader', 'Minimale werkset kerncontrols'],
  },
  '7': {
    stepNumber: '7',
    title: 'Onboarding & awareness lijnmanagement',
    description:
      'Het normenkader staat vast. Nu moet lijnmanagement weten wat er van hen verwacht wordt en in welke taal het IMS communiceert. Zonder awareness voeren ze stap 9 uit zonder te begrijpen waarom.',
    outputs: [
      'Awareness-materiaal',
      'Competentiebeoordeling',
      'Documentbeheerprocedure',
    ],
  },
  '8': {
    stepNumber: '8',
    title: 'Koppeling processen, systemen & verwerkingen',
    description:
      'Risicoanalyse (stap 9) vereist inzicht in welke processen welke systemen gebruiken en welke persoonsgegevens daarin zitten. Dit register legt die koppeling — zonder deze basis is de risicoanalyse incompleet.',
    outputs: [
      'Geintegreerd register',
      'PII-doorgifte-inventarisatie',
      'PbD-procedure',
    ],
  },
  '9': {
    stepNumber: '9',
    title: 'Risicoanalyse door lijnmanagement',
    description:
      'Het register is beschikbaar, de methodiek staat vast, lijnmanagement is onboarded. Nu kan de daadwerkelijke beoordeling plaatsvinden: wat zijn de risico\'s per afdeling/proces?',
    outputs: ['Risicoregister per afdeling/proces', 'BIA (BCMS-track)'],
  },
  '10': {
    stepNumber: '10',
    title: 'Risicobehandeling & controls toewijzen',
    description:
      'De risico\'s zijn bekend. Nu wordt per risico bepaald: accepteren, mitigeren, overdragen of vermijden — en worden controls en eigenaren toegewezen. Zonder dit stap blijft het risicoregister een lijst zonder actie.',
    outputs: [
      'Risicobehandelplan',
      'Controls met eigenaren',
      'Implementatieplan',
      'BCPs',
    ],
  },
  '11': {
    stepNumber: '11',
    title: 'Statement of Applicability (SoA)',
    description:
      'Met de risicoanalyse en controls in kaart kan worden vastgesteld welke ISO-controls van toepassing zijn en waarom. De SoA is het formele bewijs van een weloverwogen norm-keuze — vereist voor certificering.',
    outputs: ['SoA-document incl. ISO 27701 Annex A/B'],
  },
  '12': {
    stepNumber: '12',
    title: 'Monitoring & rapportage inrichten',
    description:
      'Het IMS is ingericht. Nu moet de infrastructuur staan om het ook te kunnen bewaken: KPI\'s, rapportagelijnen, dashboards. Zonder dit kan het SIMS in Fase 2 niet sturen op resultaten.',
    outputs: ['KPI\'s', 'Rapportagelijnen', 'Dashboards'],
  },
  '13': {
    stepNumber: '13',
    title: 'Interne audit plannen & uitvoeren',
    description:
      'Het IMS draait. Nu moet onafhankelijk worden getoetst of de controls ook daadwerkelijk werken. De audit levert de input voor de management review en toont aan dat het systeem zichzelf bewaakt.',
    outputs: [
      'Auditprogramma',
      'Auditrapportages',
      'BC-oefenrapportage',
    ],
  },
  '14': {
    stepNumber: '14',
    title: 'Management review',
    description:
      'De auditresultaten, risicostatussen en KPI\'s zijn beschikbaar. Het SIMS beoordeelt het geheel en neemt verbeterbeslissingen. Dit is het moment waarop de PDCA-cirkel sluit op strategisch niveau.',
    outputs: ['Review-rapportage', 'Verbeterbeslissingen'],
  },
  '15': {
    stepNumber: '15',
    title: 'Afwijkingen, incidenten & corrigerende maatregelen',
    description:
      'Afwijkingen en incidenten doen zich voor wanneer ze zich voordoen — niet op een gepland moment. Dit is de event-driven stap die ervoor zorgt dat problemen worden geregistreerd, geanalyseerd en opgevolgd.',
    outputs: ['Non-conformiteitenregister', 'Correctieve acties'],
  },
  '16': {
    stepNumber: '16',
    title: 'Evidence-verzameling & control-monitoring',
    description:
      'Controls zijn toegewezen en geimplementeerd. Nu moet worden bewezen dat ze ook werken: bewijs per control, continue monitoring, privacy-procedures actueel houden. Zonder evidence is een audit niet te doorstaan.',
    outputs: [
      'Bewijs per control',
      'Continue monitoring',
      'Privacy-procedures',
    ],
  },
  '17': {
    stepNumber: '17',
    title: 'PDCA-cyclus formaliseren',
    description:
      'Aan het einde van de cyclus wordt de volgende cyclus gepland. Stap 17 zorgt dat de PDCA niet stopt na een ronde maar structureel verankerd is in de jaarplanning.',
    outputs: [
      'Jaarplanning',
      'Risicoherbeoordeling',
      'Communicatieprocedures',
    ],
  },
  '18': {
    stepNumber: '18',
    title: 'Certificeringsgereedheid',
    description:
      'De organisatie wil externe validatie van het IMS. Een pre-audit brengt resterende gaps in beeld zodat de certificeringsaanvraag met vertrouwen kan worden ingediend.',
    outputs: [
      'Pre-audit rapport',
      'Gap-remediatie',
      'Certificeringsaanvraag',
    ],
  },
  '19': {
    stepNumber: '19',
    title: 'Geavanceerde analytics & rapportage',
    description:
      'Het IMS heeft genoeg historische data opgebouwd om trends te zien. Predictive risk en geautomatiseerde rapportages maken het IMS proactief in plaats van reactief.',
    outputs: [
      'Trendanalyses',
      'Predictive risk',
      'Geautomatiseerde rapportages',
    ],
  },
  '20': {
    stepNumber: '20',
    title: 'Externe integraties',
    description:
      'De organisatie werkt intensief samen met ketenpartners of leveranciers. Koppelingen maken data-uitwisseling gestructureerd en controleerbaar in plaats van handmatig.',
    outputs: ['Ketenpartner-koppelingen', 'Leveranciersportaal'],
  },
  '21': {
    stepNumber: '21',
    title: 'Multi-framework optimalisatie',
    description:
      'De organisatie werkt met meerdere normen (BIO, AVG, BCM). Cross-mapping elimineert dubbel werk: een control dekt meerdere normeisen.',
    outputs: ['Cross-mapping controls', 'Duplicatie-eliminatie'],
  },
  '22': {
    stepNumber: '22',
    title: 'Benchmarking & kennisdeling',
    description:
      'Meerdere gemeenten gebruiken het platform. Vergelijking en kennisdeling versnellen volwassenheid in de regio en maken gezamenlijk leren mogelijk.',
    outputs: ['Benchmark-rapportage', 'Best practice bibliotheek'],
  },
};

"""
Intent-based Agent Router

Hybrid routing: keyword scoring (fast) + LLM classifier (fallback).
Analyzes the user's question to pick the right agent, regardless of
which page they're on. Page context serves as a secondary boost signal.
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Result of the intent routing process."""
    agent_name: str
    method: str  # "manual", "keyword", "llm", "page_context", "default"
    confidence: float  # 0.0 – 1.0
    secondary_agents: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent keyword profiles
# ---------------------------------------------------------------------------

# Each profile: (primary_keywords weight=3, secondary_keywords weight=1, phrase_patterns weight=4)
AGENT_PROFILES: Dict[str, Dict] = {
    "risk": {
        "primary": [
            "risico", "risicos", "risk", "risks", "risicoanalyse", "risicobehandeling",
            "dreigingen", "dreiging", "threat", "kans", "likelihood", "impact",
            "heatmap", "risicomatrix", "brutorisico", "nettorisico", "restrisico",
            "risicoregister", "risicohouding", "risk appetite", "risk tolerance",
            "in control", "in-control", "mapgood",
        ],
        "secondary": [
            "gevaar", "kwetsbaarheid", "vulnerability", "accepteren", "mitigeren",
            "vermijden", "overdragen", "behandelstrategie", "treatment",
        ],
        "phrases": [
            r"welke risico", r"risico.*(hoog|laag|kritiek|midden)",
            r"(bruto|netto|rest).?risico", r"risk.*(register|matrix|appetite)",
            r"in.?control", r"wat zijn de risico",
        ],
    },
    "policy": {
        "primary": [
            "beleid", "beleidsregel", "policy", "policies", "uitgangspunt",
            "uitgangspunten", "principle", "principles", "beleidsuitgangs",
            "beleidsdocument", "beleidswijziging",
        ],
        "secondary": [
            "goedkeuring", "goedgekeurd", "approved", "draft", "concept",
            "publiceren", "published", "review", "versie", "traceerbaarheid",
            "trace", "beleidstrace",
        ],
        "phrases": [
            r"beleid.*(goedgekeurd|status|versie|concept|wijzig|aanpas)",
            r"policy.*(approved|draft|status|version)",
            r"uitgangspunt.*(toevoeg|wijzig|overzicht)",
            r"wanneer.*(beleid|policy).*(goedgekeurd|approved)",
        ],
    },
    "compliance": {
        "primary": [
            "compliance", "framework", "frameworks", "norm", "normen",
            "standaard", "standaarden", "iso", "iso27001", "iso27002",
            "bio", "nen", "soa", "verklaring van toepasselijkheid",
            "statement of applicability", "requirement", "eis", "eisen",
            "mapping", "rosetta", "control", "controls",
        ],
        "secondary": [
            "certificering", "certification", "audit", "naleving",
            "non-conformiteit", "gap", "gap-analyse",
        ],
        "phrases": [
            r"(iso|bio|nen|cis|nist).?\d",
            r"welke (norm|eis|requirement|control)",
            r"(soa|statement of applicability)",
            r"framework.*(toevoeg|mapping|vergelijk)",
            r"voldoen.*(norm|eis|standaard)",
        ],
    },
    "measure": {
        "primary": [
            "maatregel", "maatregelen", "measure", "measures", "control",
            "beheersmaatregel", "beheersmaatregelen", "implementatie",
        ],
        "secondary": [
            "effectiviteit", "effectiveness", "implementatiestatus",
            "verantwoordelijke", "eigenaar",
        ],
        "phrases": [
            r"maatregel.*(toevoeg|status|implementa|effecti)",
            r"welke maatregel", r"control.*(implement|status|effective)",
        ],
    },
    "assessment": {
        "primary": [
            "assessment", "assessments", "audit", "audits", "pentest",
            "self-assessment", "zelfevaluatie", "dpia", "evidence",
            "bewijs", "bewijsstuk", "finding", "bevinding",
        ],
        "secondary": [
            "beoordeling", "evaluatie", "toetsing", "rapportage",
            "planning", "gepland",
        ],
        "phrases": [
            r"status.*(dpia|assessment|audit|pentest)",
            r"(dpia|assessment|audit).*(starten|plannen|resultaat|status)",
            r"wanneer.*(audit|assessment|pentest)",
            r"bevinding.*(open|gesloten|status)",
        ],
    },
    "incident": {
        "primary": [
            "incident", "incidenten", "datalek", "datalekken", "breach",
            "melding", "beveiligingsincident", "security incident",
        ],
        "secondary": [
            "respons", "response", "escalatie", "escalation", "melden",
            "afhandeling", "impact", "calamiteit",
        ],
        "phrases": [
            r"incident.*(meld|registr|status|afhandel|open)",
            r"datalek.*(meld|registr|ap|autoriteit)",
            r"hoeveel incident",
        ],
    },
    "privacy": {
        "primary": [
            "privacy", "avg", "gdpr", "persoonsgegevens", "verwerking",
            "verwerkingsregister", "betrokkene", "data subject",
            "verwerkingsovereenkomst", "verwerkersovereenkomst",
            "dpia", "pia", "gegevensbescherming",
        ],
        "secondary": [
            "toestemming", "consent", "recht op", "inzage", "verwijdering",
            "portabiliteit", "ap", "autoriteit persoonsgegevens",
        ],
        "phrases": [
            r"(avg|gdpr).*(verplichting|eis|nalev)",
            r"privacy.*(beleid|impact|risico|register)",
            r"verwerk.*(register|overeenkomst|grondslag)",
            r"recht.*(inzage|verwijder|verget)",
        ],
    },
    "bcm": {
        "primary": [
            "continuiteit", "continuity", "bcm", "bcms", "bia",
            "business impact", "noodplan", "calamiteitenplan",
            "uitwijkplan", "herstelplan", "recovery", "rto", "rpo",
        ],
        "secondary": [
            "beschikbaarheid", "availability", "uitval", "storing",
            "backup", "disaster", "noodscenario",
        ],
        "phrases": [
            r"(bia|business impact).*(analyse|resultaat|score)",
            r"continu.*(plan|test|oefening)",
            r"(rto|rpo).*(wat|waarde|bepaal)",
            r"uitwijk.*(plan|locatie|test)",
        ],
    },
    "scope": {
        "primary": [
            "scope", "scopes", "asset", "assets", "proces", "processen",
            "organisatie", "cluster", "afhankelijkheid", "dependency",
        ],
        "secondary": [
            "hierarchie", "structuur", "onderdeel", "bedrijfsonderdeel",
            "afdeling", "locatie",
        ],
        "phrases": [
            r"scope.*(toevoeg|wijzig|overzicht|structuur)",
            r"asset.*(toevoeg|overzicht|classificat)",
            r"welke (proces|asset|scope)",
            r"afhankelijkhe.*(tussen|van|toon)",
        ],
    },
    "supplier": {
        "primary": [
            "leverancier", "leveranciers", "supplier", "suppliers",
            "derde partij", "third party", "vendor", "uitbesteding",
            "outsourcing",
        ],
        "secondary": [
            "contract", "sla", "beoordeling", "classificatie",
        ],
        "phrases": [
            r"leverancier.*(toevoeg|beoordelel|risico|overzicht)",
            r"third.?party.*(risk|management|assess)",
        ],
    },
    "improvement": {
        "primary": [
            "verbetering", "verbeterplan", "correctieve", "corrective",
            "actie", "action", "afwijking", "exception", "waiver",
            "uitzondering", "pdca", "feedbackloop",
        ],
        "secondary": [
            "deadline", "overdue", "achterstallig", "vervolgactie",
            "opvolging",
        ],
        "phrases": [
            r"(correctieve|verbeter).*(actie|maatregel|plan)",
            r"actie.*(open|overdue|achterstallig|status)",
            r"uitzondering.*(aanvrag|registr|goedkeur)",
        ],
    },
    "workflow": {
        "primary": [
            "workflow", "goedkeuring", "approval", "status",
            "statusovergang", "transition", "accordering",
        ],
        "secondary": [
            "wachten op", "pending", "afgewezen", "rejected",
        ],
        "phrases": [
            r"workflow.*(stap|status|configureer)",
            r"goedkeuring.*(aanvrag|wacht|status)",
        ],
    },
    "planning": {
        "primary": [
            "planning", "roadmap", "backlog", "sprint", "mijlpaal",
            "milestone", "tijdlijn", "timeline", "jaarplan",
        ],
        "secondary": [
            "prioriteit", "priority", "capaciteit", "resource",
        ],
        "phrases": [
            r"planning.*(overzicht|toevoeg|wijzig)",
            r"roadmap.*(toon|bijwerk|status)",
            r"backlog.*(item|priorit)",
        ],
    },
    "report": {
        "primary": [
            "rapport", "rapportage", "report", "reporting", "dashboard",
            "grafiek", "chart", "statistieken", "samenvatting",
            "managementrapportage", "export",
        ],
        "secondary": [
            "kpi", "metric", "trend", "overzicht",
        ],
        "phrases": [
            r"rapport.*(genere|export|toon|overzicht)",
            r"dashboard.*(toon|configureer|widget)",
            r"management.?rapport",
        ],
    },
    "objectives": {
        "primary": [
            "doelstelling", "doelstellingen", "objective", "objectives",
            "kpi", "kpis", "doel", "doelen", "target", "indicator",
        ],
        "secondary": [
            "prestatie", "performance", "meetbaar", "voortgang",
        ],
        "phrases": [
            r"doelstelling.*(toevoeg|status|voortgang)",
            r"kpi.*(waarde|meet|rapporteer|definieer)",
        ],
    },
    "maturity": {
        "primary": [
            "maturity", "volwassenheid", "volwassenheidsniveau",
            "maturity model", "cmmi", "capability",
        ],
        "secondary": [
            "niveau", "level", "assessment", "benchmark",
        ],
        "phrases": [
            r"(maturity|volwassenheid).*(niveau|model|assess|score)",
        ],
    },
    "admin": {
        "primary": [
            "admin", "administratie", "gebruiker", "gebruikers",
            "user", "users", "rol", "rollen", "role", "roles",
            "rechten", "permission", "configuratie",
        ],
        "secondary": [
            "tenant", "instelling", "settings", "licentie",
        ],
        "phrases": [
            r"gebruiker.*(toevoeg|wijzig|verwijder|rol)",
            r"rol.*(toewijz|wijzig|aanmak)",
            r"(rechten|permission).*(instell|wijzig)",
        ],
    },
    "onboarding": {
        "primary": [
            "onboarding", "welkom", "starten", "organisatie instellen",
            "eerste stappen", "setup", "wizard",
        ],
        "secondary": [
            "profiel", "account", "configuratie",
        ],
        "phrases": [
            r"hoe begin ik", r"eerste stappen",
            r"organisatie.*(instell|configureer)",
        ],
    },
}

# Pre-compile phrase patterns
_COMPILED_PHRASES: Dict[str, List[re.Pattern]] = {}
for _agent, _profile in AGENT_PROFILES.items():
    _COMPILED_PHRASES[_agent] = [
        re.compile(p, re.IGNORECASE) for p in _profile.get("phrases", [])
    ]


class KeywordScorer:
    """
    Fast first-pass: scores a message against every agent's keyword profile.
    Returns sorted list of (agent_name, score) tuples.
    """

    WEIGHT_PRIMARY = 3
    WEIGHT_SECONDARY = 1
    WEIGHT_PHRASE = 4
    WEIGHT_PAGE_BOOST = 2

    def score(
        self,
        message: str,
        page_agent: Optional[str] = None,
    ) -> Tuple[List[Tuple[str, float]], bool]:
        """Score the message against all agent profiles.

        Returns:
            (scores, has_keyword_matches) where scores is a list of
            (agent_name, normalised_score) sorted descending, and
            has_keyword_matches indicates if any real keyword/phrase
            matched (not just the page boost).
        """
        msg_lower = message.lower()
        # Tokenize for word matching
        words = set(re.findall(r"\w+", msg_lower))

        scores: Dict[str, int] = {}
        has_keyword_matches = False

        for agent_name, profile in AGENT_PROFILES.items():
            raw = 0

            # Primary keywords
            for kw in profile["primary"]:
                if kw in words or kw in msg_lower:
                    raw += self.WEIGHT_PRIMARY
                    has_keyword_matches = True

            # Secondary keywords
            for kw in profile["secondary"]:
                if kw in words or kw in msg_lower:
                    raw += self.WEIGHT_SECONDARY
                    has_keyword_matches = True

            # Phrase patterns
            for pattern in _COMPILED_PHRASES[agent_name]:
                if pattern.search(msg_lower):
                    raw += self.WEIGHT_PHRASE
                    has_keyword_matches = True

            # Page context boost
            if page_agent and agent_name == page_agent:
                raw += self.WEIGHT_PAGE_BOOST

            if raw > 0:
                scores[agent_name] = raw

        if not scores:
            return [], False

        max_score = max(scores.values())
        normalised = [
            (name, round(s / max_score, 3)) for name, s in scores.items()
        ]
        normalised.sort(key=lambda x: x[1], reverse=True)
        return normalised, has_keyword_matches


class LLMClassifier:
    """
    Fallback classifier: uses the configured LLM to determine the right agent.
    Only called when keyword scoring is ambiguous.
    """

    CLASSIFICATION_PROMPT = """Je bent een router voor een GRC-platform (Governance, Risk & Compliance).
Bepaal welke expert-agent het beste past bij de vraag van de gebruiker.

Beschikbare agents:
- risk: Risicomanagement, risicoanalyse, heatmap, in-control, MAPGOOD, behandelstrategieën
- policy: Beleid, beleidsregels, uitgangspunten, goedkeuringsworkflow
- compliance: Frameworks (ISO, BIO, NEN), normen, eisen, SoA, requirement mappings
- measure: Maatregelen, beheersmaatregelen, implementatie, effectiviteit
- assessment: Assessments, audits, pentests, DPIA uitvoering, bevindingen, bewijsstukken
- incident: Incidenten, datalekken, meldingen, response
- privacy: AVG/GDPR, verwerkingsregister, persoonsgegevens, rechten betrokkenen
- bcm: Business continuity, BIA, noodplannen, RTO/RPO, uitwijkplannen
- scope: Scope, assets, processen, organisatiestructuur, afhankelijkheden
- supplier: Leveranciersbeheer, derde partijen, contracten
- improvement: Verbeteracties, correctieve maatregelen, afwijkingen, uitzonderingen
- workflow: Statusovergangen, goedkeuringen, accordering
- planning: Planning, roadmaps, backlog, mijlpalen
- report: Rapportages, dashboards, grafieken, statistieken, export
- objectives: Doelstellingen, KPIs, prestatie-indicatoren
- maturity: Volwassenheidsniveaus, maturity assessments
- admin: Gebruikersbeheer, rollen, rechten, configuratie
- onboarding: Eerste stappen, organisatie instellen, welkom

Huidige pagina: {page}

Gebruikersvraag: {message}

Antwoord met ALLEEN de agent-naam (bijv. "risk" of "policy"). Niets anders."""

    async def classify(
        self,
        message: str,
        page: str = "",
        timeout_seconds: float = 3.0,
    ) -> Optional[str]:
        """Classify a message using the LLM. Returns agent name or None on failure."""
        try:
            from app.services.ai_gateway import ai_gateway

            llm = ai_gateway.get_llm()
            prompt = self.CLASSIFICATION_PROMPT.format(
                page=page or "onbekend",
                message=message,
            )

            result = await asyncio.wait_for(
                llm.ainvoke(prompt),
                timeout=timeout_seconds,
            )

            agent_name = result.content.strip().lower().replace('"', "").replace("'", "")
            # Validate the agent name
            if agent_name in AGENT_PROFILES:
                return agent_name

            logger.warning(f"LLM classifier returned unknown agent: {agent_name}")
            return None

        except asyncio.TimeoutError:
            logger.warning("LLM classifier timed out")
            return None
        except Exception as e:
            logger.warning(f"LLM classifier error: {e}")
            return None


class IntentRouter:
    """
    Coordinates routing: manual override → keyword → LLM fallback → page → default.
    """

    CONFIDENCE_THRESHOLD = 0.6
    AMBIGUITY_GAP = 0.15  # min gap between #1 and #2 to be considered unambiguous

    def __init__(self):
        self.keyword_scorer = KeywordScorer()
        self.llm_classifier = LLMClassifier()

    async def route(
        self,
        message: str,
        page: Optional[str] = None,
        entity_type: Optional[str] = None,
        manual_override: Optional[str] = None,
    ) -> RoutingDecision:
        """
        Determine the best agent for a user message.

        Priority:
        1. Manual override (user explicitly selected an agent)
        2. Keyword scoring with high confidence
        3. LLM classifier (for ambiguous cases)
        4. Page context fallback
        5. Default: "risk"
        """

        # 1. Manual override
        if manual_override:
            return RoutingDecision(
                agent_name=manual_override,
                method="manual",
                confidence=1.0,
            )

        # Determine page-based agent for boost / fallback
        page_agent = self._page_to_agent(page, entity_type)

        # 2. Keyword scoring
        scores, has_keyword_matches = self.keyword_scorer.score(
            message, page_agent=page_agent
        )

        if scores and has_keyword_matches:
            top_name, top_score = scores[0]
            secondary = [s[0] for s in scores[1:4]]

            # High confidence and clear winner
            if top_score >= self.CONFIDENCE_THRESHOLD:
                is_ambiguous = (
                    len(scores) >= 2
                    and (top_score - scores[1][1]) < self.AMBIGUITY_GAP
                )

                if not is_ambiguous:
                    return RoutingDecision(
                        agent_name=top_name,
                        method="keyword",
                        confidence=top_score,
                        secondary_agents=secondary,
                    )

                # 3. Ambiguous → LLM fallback
                llm_result = await self.llm_classifier.classify(message, page or "")
                if llm_result:
                    return RoutingDecision(
                        agent_name=llm_result,
                        method="llm",
                        confidence=0.8,
                        secondary_agents=secondary,
                    )

                # LLM failed → use keyword winner anyway
                return RoutingDecision(
                    agent_name=top_name,
                    method="keyword",
                    confidence=top_score,
                    secondary_agents=secondary,
                )

        # 4. No keyword matches → page context
        if page_agent:
            return RoutingDecision(
                agent_name=page_agent,
                method="page_context",
                confidence=0.4,
            )

        # 5. Default
        return RoutingDecision(
            agent_name="risk",
            method="default",
            confidence=0.2,
        )

    @staticmethod
    def _page_to_agent(page: Optional[str], entity_type: Optional[str] = None) -> Optional[str]:
        """Map page/entity to agent name (lightweight, no orchestrator dependency)."""
        from app.agents.core.orchestrator import AgentOrchestrator

        if page:
            page_lower = page.lower()
            for key, agent_name in AgentOrchestrator.CONTEXT_AGENT_MAP.items():
                if key in page_lower:
                    return agent_name

        if entity_type:
            entity_lower = entity_type.lower()
            if entity_lower in AgentOrchestrator.CONTEXT_AGENT_MAP:
                return AgentOrchestrator.CONTEXT_AGENT_MAP[entity_lower]

        return None

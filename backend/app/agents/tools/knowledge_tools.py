"""
Knowledge Tools for AI Agents.

These tools provide access to the knowledge base and methodologies.
Used for looking up standards, frameworks, and best practices.
"""
from typing import Optional
from langchain_core.tools import tool
from app.core.db import get_session
from app.services.knowledge_service import knowledge_service


@tool
async def search_knowledge(query: str, limit: int = 3) -> str:
    """
    Search the internal knowledge base using semantic search.

    Use this to find information about:
    - Methodologies (In Control, MAPGOOD)
    - Standards (BIO, ISO 27001, AVG)
    - Best practices and guidance
    - Policies and procedures
    """
    async for session in get_session():
        results = await knowledge_service.search_knowledge(session, query, limit=limit)

        if not results:
            return f"No knowledge found for query: '{query}'"

        output = f"Found {len(results)} relevant knowledge items:\n\n"
        for item in results:
            output += f"📚 **{item.title}** (Category: {item.category})\n"
            output += f"{item.content[:500]}{'...' if len(item.content) > 500 else ''}\n"
            output += "---\n"

        return output


@tool
def get_methodology(methodology_name: str) -> str:
    """
    Get information about a specific risk management methodology.

    Supported methodologies:
    - in_control: The In Control risk quadrant model
    - mapgood: MAPGOOD threat categorization
    - bio: Baseline Informatiebeveiliging Overheid
    - iso27001: ISO 27001 Information Security
    - avg: AVG/GDPR Privacy regulation
    """
    methodologies = {
        "in_control": """
## In Control Model

The In Control model classifies risks into four quadrants based on Impact and Vulnerability:

| Impact/Vulnerability | High Impact | Low Impact |
|---------------------|-------------|------------|
| High Vulnerability  | MITIGATE    | MONITOR    |
| Low Vulnerability   | ASSURANCE   | ACCEPT     |

**Quadrant Actions:**
- **MITIGATE**: High impact, high vulnerability. Requires active measures to reduce risk.
- **ASSURANCE**: High impact, low vulnerability. Already well-controlled, maintain assurance activities.
- **MONITOR**: Low impact, high vulnerability. Keep an eye on, may need attention if situation changes.
- **ACCEPT**: Low impact, low vulnerability. Risk is acceptable, document the acceptance.
""",
        "mapgood": """
## MAPGOOD Dreigingscategorieën

MAPGOOD is a Dutch framework for categorizing security threats:

- **M**enselijk handelen (Human actions) - Intentional or unintentional human errors
- **A**pplicaties (Applications) - Software vulnerabilities and bugs
- **P**rocessen (Processes) - Process failures and gaps
- **G**egevens (Data) - Data quality and integrity issues
- **O**mgeving (Environment) - Physical and environmental threats
- **O**pzet (Intentional) - Deliberate attacks and malicious actions
- **D**erden (Third parties) - Supplier and partner risks

Each risk should be categorized using these categories to ensure comprehensive coverage.
""",
        "bio": """
## BIO - Baseline Informatiebeveiliging Overheid

The BIO is the Dutch government's baseline for information security, based on ISO 27001/27002.

**Key domains:**
1. Information Security Policies
2. Organization of Information Security
3. Human Resource Security
4. Asset Management
5. Access Control
6. Cryptography
7. Physical and Environmental Security
8. Operations Security
9. Communications Security
10. System Acquisition, Development and Maintenance
11. Supplier Relationships
12. Incident Management
13. Business Continuity
14. Compliance

**Classification levels:**
- BBN1: Basic
- BBN2: Standard (most common for municipalities)
- BBN3: High security
""",
        "iso27001": """
## ISO 27001 - Information Security Management System

ISO 27001 is the international standard for information security management.

**Key components:**
- **Context**: Understanding the organization and stakeholder needs
- **Leadership**: Management commitment and policy
- **Planning**: Risk assessment and treatment
- **Support**: Resources, competence, awareness, communication
- **Operation**: Implementing risk treatment plans
- **Performance evaluation**: Monitoring, measurement, analysis
- **Improvement**: Nonconformity handling and continual improvement

**Annex A controls:** 93 controls across 4 themes:
- Organizational controls (37)
- People controls (8)
- Physical controls (14)
- Technological controls (34)
""",
        "avg": """
## AVG/GDPR - Algemene Verordening Gegevensbescherming

The Dutch implementation of GDPR for personal data protection.

**Key principles:**
1. Lawfulness, fairness and transparency
2. Purpose limitation
3. Data minimization
4. Accuracy
5. Storage limitation
6. Integrity and confidentiality
7. Accountability

**Legal bases for processing:**
- Consent
- Contract
- Legal obligation
- Vital interests
- Public task
- Legitimate interest

**Data subject rights:**
- Right of access
- Right to rectification
- Right to erasure
- Right to restriction
- Right to data portability
- Right to object
- Rights related to automated decision-making

**Breach notification:** Within 72 hours to Autoriteit Persoonsgegevens if risk to data subjects.
"""
    }

    key = methodology_name.lower().replace(" ", "_").replace("-", "_")
    if key in methodologies:
        return methodologies[key]
    else:
        available = ", ".join(methodologies.keys())
        return f"Unknown methodology '{methodology_name}'. Available: {available}"


@tool
def classify_risk_quadrant(impact: str, vulnerability: str) -> str:
    """
    Determine the In Control risk quadrant based on Impact and Vulnerability.

    Parameters:
    - impact: HIGH or LOW
    - vulnerability: HIGH or LOW

    Returns the appropriate quadrant and recommended actions.
    """
    impact = impact.upper()
    vulnerability = vulnerability.upper()

    if impact not in ["HIGH", "LOW"] or vulnerability not in ["HIGH", "LOW"]:
        return "Invalid input. Both impact and vulnerability must be 'HIGH' or 'LOW'."

    quadrant_info = {
        ("HIGH", "HIGH"): {
            "quadrant": "MITIGATE",
            "description": "High impact and high vulnerability - requires active risk mitigation.",
            "actions": [
                "Implement additional security measures",
                "Create corrective action plan",
                "Assign risk owner and set deadlines",
                "Monitor progress closely",
            ]
        },
        ("HIGH", "LOW"): {
            "quadrant": "ASSURANCE",
            "description": "High impact but low vulnerability - maintain current controls and verify effectiveness.",
            "actions": [
                "Schedule regular audits/assessments",
                "Document existing controls",
                "Collect evidence of control effectiveness",
                "Monitor for changes in vulnerability",
            ]
        },
        ("LOW", "HIGH"): {
            "quadrant": "MONITOR",
            "description": "Low impact but high vulnerability - keep under observation.",
            "actions": [
                "Set up monitoring/alerting",
                "Review periodically",
                "Escalate if impact increases",
                "Consider low-cost mitigations",
            ]
        },
        ("LOW", "LOW"): {
            "quadrant": "ACCEPT",
            "description": "Low impact and low vulnerability - risk is acceptable.",
            "actions": [
                "Document risk acceptance",
                "Get management sign-off if required",
                "Set review date",
                "No active mitigation needed",
            ]
        },
    }

    info = quadrant_info[(impact, vulnerability)]

    output = f"""
## Risk Classification Result

**Quadrant: {info['quadrant']}**

{info['description']}

**Recommended Actions:**
"""
    for i, action in enumerate(info['actions'], 1):
        output += f"{i}. {action}\n"

    return output

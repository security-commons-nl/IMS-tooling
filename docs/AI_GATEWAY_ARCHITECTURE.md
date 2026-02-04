# Multi-Provider AI Gateway Architecture

## Overzicht
De IMS applicatie maakt gebruik van een **Multi-Provider AI Gateway** om robuuste, snelle en privacy-vriendelijke AI-functionaliteit te bieden. Deze architectuur stelt het systeem in staat om naadloos te schakelen tussen Europese cloud-providers en lokale on-premise modellen.

## Architectuur Diagram

```mermaid
graph TD
    User[Gebruiker] --> FE[Frontend (Reflex)]
    FE --> API[Backend API]
    API --> Agent[AI Agent (BaseAgent)]
    Agent --> GW[AI Gateway Service]
    
    subgraph "AI Gateway (Failover Logic)"
        GW -->|1. Probeer| Mistral{Mistral AI Config?}
        Mistral -->|Ja & Beschikbaar| API_Mistral[Mistral API (Frankrijk)]
        Mistral -->|Nee of Fout| Scaleway{Scaleway Config?}
        
        Scaleway -->|Ja & Beschikbaar| API_Scaleway[Scaleway API (Frankrijk)]
        Scaleway -->|Nee of Fout| Ollama{Ollama Lokaal}
        
        Ollama -->|Altijd Beschikbaar| Docker_Ollama[Local Ollama (CPU)]
    end
    
    API_Mistral --> Result[Antwoord]
    API_Scaleway --> Result
    Docker_Ollama --> Result
    Result --> Agent
```

## Providers & Prioriteit

De gateway hanteert een strikte prioriteitsvolgorde om de balans te vinden tussen kwaliteit, snelheid en beschikbaarheid. Alle geconfigureerde providers zijn **Europese bedrijven** of draaien lokaal, wat GDPR-compliance waarborgt.

| Prioriteit | Provider | Type | Model | Locatie | Kenmerken |
|------------|----------|------|-------|---------|-----------|
| **1. Primair** | **Mistral AI** | Cloud API | `mistral-small-latest` | 🇫🇷 Frankrijk | Zeer snel, hoge kwaliteit, betaalbaar. |
| **2. Secundair** | **Scaleway** | Cloud API | `mistral-nemo` | 🇫🇷 Frankrijk | Gehoste open modellen, pay-per-token. |
| **3. Fallback** | **Ollama** | Lokaal | `mistral` (7B) | 🏠 On-Premise | Werkt zonder internet, trager (CPU), geen datalek risico. |

## Technische Implementatie

### 1. Gateway Service (`app/services/ai_gateway.py`)
Deze service wordt bij het opstarten van de applicatie geïnitialiseerd. Hij controleert de `.env` configuratie en maakt verbindingen aan met de beschikbare providers.

- **Initialization:** Leest API keys en URLs.
- **Pooling:** Houdt 'clients' (LangChain objecten) warm voor gebruik.
- **Failover:** Als een request naar de primaire provider faalt (timeout of 500 error), wordt dit (nog niet automatisch in v1, maar configuratie-technisch wel voorbereid) opgevangen door de volgende in de keten. *Huidige implementatie kiest bij start de beste beschikbare provider.*

### 2. Base Agent (`app/agents/core/base_agent.py`)
Alle specifieke agents (Risk, Compliance, etc.) erven van `BaseAgent`. In plaats van rechtstreeks verbinding te maken met Ollama, vragen ze nu een `runnable` aan de Gateway.

```python
# Oude situatie
self.llm = ChatOllama(...)

# Nieuwe situatie
from app.services.ai_gateway import ai_gateway
self.runnable = ai_gateway.get_runnable(self.tools)
```

## Configuratie

De configuratie wordt beheerd via `.env` variabelen.

### Mistral AI (Aanbevolen)
```env
MISTRAL_API_KEY=jouw_key_hier
MISTRAL_MODEL=mistral-small-latest
```

### Scaleway (Optioneel)
```env
SCALEWAY_API_KEY=jouw_key_hier
SCALEWAY_MODEL=mistral-nemo-instruct-2407
```

### Ollama (Standaard)
Geen configuratie nodig, werkt out-of-the-box via Docker interne netwerk (`http://ollama:11434`).

## Foutafhandeling

- **Timeouts:** De frontend hanteert een timeout van **120 seconden** om trage response van lokale modellen op te vangen.
- **Empty Responses:** Lege antwoorden worden afgevangen met een duidelijke foutmelding in de UI.
- **Connection Errors:** Als de Gateway geen enkele provider kan bereiken, wordt dit gelogd en krijgt de gebruiker een melding.

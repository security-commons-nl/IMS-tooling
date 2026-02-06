title:	Enable AI Agent Tool Execution and Safety Tools
state:	OPEN
author:	Treason8579
labels:	
assignees:	
reviewers:	
projects:	
milestone:	
number:	4
url:	https://github.com/lugdunium/IMS/pull/4
additions:	360
deletions:	24
auto-merge:	disabled
--
This PR enables the "Brain" of the AI agents by allowing them to actually execute the tools they select. Previously, agents could only select tools but not run them. 

Key changes:
1.  **Tool Execution Loop:** `BaseAgent.chat` now handles the ReAct loop: invoking the LLM, checking for tool calls, executing them, and feeding results back.
2.  **Safety & Security:** 
    - `create_suggestion` tool implemented to allow agents to propose changes safely without direct write access.
    - Tenant ID is now injected via `ContextVar` instead of being a parameter exposed to the LLM, preventing cross-tenant write risks.
3.  **New Tools:** Added `request_agent_collaboration` to allow agents to consult each other.
4.  **Logging:** Improved logging in `AgentOrchestrator`.

Tests added in `backend/tests/test_agent_execution.py`.

---
*PR created automatically by Jules for task [12662966546079237698](https://jules.google.com/task/12662966546079237698) started by @Treason8579*

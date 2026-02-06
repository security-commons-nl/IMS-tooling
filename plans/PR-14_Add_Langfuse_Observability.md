title:	Add Langfuse observability integration for LLM providers
state:	OPEN
author:	Treason8579
labels:	codex
assignees:	
reviewers:	
projects:	
milestone:	
number:	14
url:	https://github.com/lugdunium/IMS/pull/14
additions:	28
deletions:	0
auto-merge:	disabled
--
### Motivation
- Provide LLM observability by integrating Langfuse so requests and model interactions can be tracked across configured providers.
- Make Langfuse configurable via environment variables so observability can be enabled or disabled per-deployment.

### Description
- Added Langfuse settings (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`) to `backend/app/core/config.py` and example env vars to `.env.example`.
- Added `langfuse>=2.0.0` to `backend/requirements.txt` so the Langfuse SDK is available.
- Wired a `CallbackHandler` from `langfuse.langchain` into `backend/app/services/ai_gateway.py`, exporting the Langfuse keys to `os.environ`, creating a `callbacks` list, and passing `callbacks=callbacks` to `ChatMistralAI`, `ChatOpenAI` (Scaleway), and `ChatOllama` during provider initialization with init-time logging and error handling.

### Testing
- No automated tests were run for this change.

------
[Codex Task](https://chatgpt.com/codex/tasks/task_e_69848d5ba1f08329aa999d3170a2b05f)

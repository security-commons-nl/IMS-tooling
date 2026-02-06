title:	Monte Carlo Simulation for Risk Analysis
state:	OPEN
author:	Treason8579
labels:	
assignees:	
reviewers:	
projects:	
milestone:	
number:	15
url:	https://github.com/lugdunium/IMS/pull/15
additions:	953
deletions:	0
auto-merge:	disabled
--
Implemented Monte Carlo simulation feature.
1.  **Backend**:
    *   Added `RiskQuantificationProfile` to `core_models.py` to store tenant-specific settings for Low/Med/High/Critical frequency and impact ranges.
    *   Created `api/v1/endpoints/simulation.py` to handle configuration (CRUD) and execution (`/run`).
    *   The simulation maps qualitative risk levels to quantitative ranges and runs N iterations (default 10k) to calculate annual loss distribution, VaR 95/99, and Expected Loss.
2.  **Frontend**:
    *   Created `ims/pages/simulation.py` with tabs for "Simulatie" (Dashboard) and "Instellingen" (Config).
    *   Created `ims/state/simulation.py` to manage state.
    *   Added simple histogram visualization using Flexbox.
3.  **Tests**:
    *   Added `backend/tests/test_simulation.py` to verify API logic.

---
*PR created automatically by Jules for task [6399181020289044511](https://jules.google.com/task/6399181020289044511) started by @Treason8579*

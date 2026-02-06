title:	⚡ Optimize SoA linking (Fix N+1 query)
state:	OPEN
author:	Treason8579
labels:	
assignees:	
reviewers:	
projects:	
milestone:	
number:	8
url:	https://github.com/lugdunium/IMS/pull/8
additions:	107
deletions:	10
auto-merge:	disabled
--
💡 **What:**
Optimized `backend/app/api/v1/endpoints/soa.py` to fix an N+1 query issue in the `link_measure_to_requirements` function. Replaced the loop that queried the database for each requirement ID with a single query using the `IN` clause. Also added defensive coding to handle missing model attributes (`local_measure_id`, `shared_measure_id`) that were causing crashes on update.

🎯 **Why:**
The original code executed a database query for every requirement in the list. For 50 requirements, this meant 50 SELECT queries. This is inefficient and scales linearly with the number of requirements. The model definition was also out of sync with the code, causing runtime errors when updating existing entries.

📊 **Measured Improvement:**
- **Baseline:** ~102 queries for 50 requirements (50 SELECTs + 50 INSERTs + overhead).
- **Optimized:** ~53 queries for creation (1 SELECT + 50 INSERTs + overhead), and ~4 queries for updates (1 SELECT + overhead).
- **Reduction:** 98% reduction in read queries (from 50 to 1).
- **Bug Fix:** Fixed a crash on the update path where `local_measure_id` was being accessed on the model which does not define it.


---
*PR created automatically by Jules for task [11416783800756512557](https://jules.google.com/task/11416783800756512557) started by @Treason8579*

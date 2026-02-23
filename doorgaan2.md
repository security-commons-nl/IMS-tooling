Fixing Decision Creation Error and Verifying Entity Actions
The user reports a 500 error when creating a decision. Analysis suggests that the frontend sends the date in a non-ISO format ("DD/MM/YYYY"), which crashes the backend. This plan fixes the date handling and ensures other entity flows are healthy.

User Review Required
WARNING

I am assuming the 500 error is caused by the date format mismatch. If the fix doesn't resolve the issue, I will need to look deeper into the backend database constraints.

Proposed Changes
Frontend
[MODIFY] 
decision.py
Add a helper method to normalize date strings to ISO format (YYYY-MM-DD).
Use this helper in 
save_decision
 before sending 
valid_until
 to the API.
Backend
[MODIFY] 
core_models.py
Add a @field_validator('valid_until', mode='before') to the 
Decision
 model to gracefully handle both ISO and European date formats during Pydantic validation. This provides a safety net if the frontend sends a non-ISO string.
Verification Plan
Automated Tests
New Backend Test: Create backend/tests/test_decisions.py to test decision creation with different date formats (YYYY-MM-DD and DD/MM/YYYY).
Run command: pytest backend/tests/test_decisions.py
Existing Risk Tests: Run pytest backend/tests/test_risks.py to ensure no regression.
Manual Verification
Decision Creation:
Open Decisions page.
Fill in a decision with a date like 19/11/2026.
Verify it saves successfully.
Entity Consistency:
Test creating a Risk on the Risks page.
Test creating a Control on the Controls page.
Verify both function correctly and data shows up in the tables.
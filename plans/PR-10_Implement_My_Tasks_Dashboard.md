title:	Add My Tasks Dashboard Endpoint
state:	OPEN
author:	Treason8579
labels:	
assignees:	
reviewers:	
projects:	
milestone:	
number:	10
url:	https://github.com/lugdunium/IMS/pull/10
additions:	253
deletions:	0
auto-merge:	disabled
--
Added a new endpoint `/api/v1/dashboard/my-tasks` to retrieve a unified list of tasks for a specific user. This includes open Corrective Actions, upcoming Review Schedules, and active Workflow Instances (approvals and tasks). Added unit tests to verify the aggregation logic.

---
*PR created automatically by Jules for task [14846062854498413558](https://jules.google.com/task/14846062854498413558) started by @Treason8579*

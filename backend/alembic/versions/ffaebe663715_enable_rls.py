"""enable_rls

Revision ID: ffaebe663715
Revises: 016_remove_treatment
Create Date: 2026-02-11 10:20:45.596700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'ffaebe663715'
down_revision: Union[str, None] = '016_remove_treatment'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables with mandatory tenant_id (Strict isolation)
STRICT_TABLES = [
    "scope",
    "scopedependency",
    "risk",
    "riskquantificationprofile",
    "control",
    "incident",
    "exception",
    "assessment",
    "evidence",
    "assessmentresponse",
    "finding",
    "correctiveaction",
    "processingactivity",
    "datasubjectrequest",
    "processoragreement",
    "continuityplan",
    "continuitytest",
    "document",
    "riskappetite",
    "managementreview",
    "complianceplanningitem",
    "initiative",
    "reviewschedule",
    "auditlog",
    "notification",
    "comment",
    "attachment",
    "maturityassessment",
    "policy",
    "organizationcontext",
    "organizationprofile",
    "knowledgeartifact",
    "dashboard",
    "aitoolexecution",
    "aiconversation",
    "aisuggestion",
    "objective",
    "tag",
    "entitytag",
    "tenantsetting",
    "integrationconfig",
    "reporttemplate",
    "scheduledreport",
    "reportexecution",
    "workflowinstance",
    "backlogitem", 
    "userscoperole",
    "standard", 
    "requirement"
]

# Tables with optional tenant_id (NULL = Global/Shared)
SHARED_TABLES = [
    "assessmentquestion",
    "biathreshold",
    "aiknowledgebase",
    "aiprompttemplate",
    "aiagent",
    "workflowdefinition"
]

def upgrade() -> None:
    # 1. Enable RLS and Add Policy for STRICT tables
    for table in STRICT_TABLES:
        try:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
            op.execute(f"""
                CREATE POLICY tenant_isolation ON {table}
                USING (tenant_id = current_setting('app.current_tenant')::integer);
            """)
        except Exception as e:
            # We catch errors to avoid failing the whole migration if one table is missing or fails
            # But in production we might want to fail hard. For now, printing key info.
            print(f"ERROR: Could not enable RLS on {table}: {e}")
            raise e

    # 2. Enable RLS and Add Policy for SHARED tables
    for table in SHARED_TABLES:
        try:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};") 
            op.execute(f"""
                CREATE POLICY tenant_isolation ON {table}
                USING (
                    tenant_id = current_setting('app.current_tenant')::integer 
                    OR tenant_id IS NULL
                );
            """)
        except Exception as e:
            print(f"ERROR: Could not enable RLS on {table}: {e}")
            raise e


def downgrade() -> None:
    # Disable RLS and Remove Policies
    for table in STRICT_TABLES + SHARED_TABLES:
        try:
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        except Exception as e:
            print(f"Warning: Could not disable RLS on {table}: {e}")

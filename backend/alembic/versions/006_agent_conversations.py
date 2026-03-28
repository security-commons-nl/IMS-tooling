"""Add agent conversation and message tables

Revision ID: 006
Revises: 005
Create Date: 2026-03-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # agent_conversations — tenant-scoped
    # ------------------------------------------------------------------
    op.create_table(
        "agent_conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column(
            "step_execution_id",
            UUID(as_uuid=True),
            sa.ForeignKey("ims_step_executions.id"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="active"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "step_execution_id",
            "agent_name",
            name="uq_conversation_tenant_execution_agent",
        ),
    )
    op.create_index(
        "ix_conversations_execution_id",
        "agent_conversations",
        ["step_execution_id"],
    )

    # ------------------------------------------------------------------
    # agent_messages
    # ------------------------------------------------------------------
    op.create_table(
        "agent_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_conversations.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column(
            "audit_log_id",
            UUID(as_uuid=True),
            sa.ForeignKey("ai_audit_logs.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_messages_conversation_id",
        "agent_messages",
        ["conversation_id"],
    )

    # ------------------------------------------------------------------
    # RLS on both tables
    # ------------------------------------------------------------------
    for table in ("agent_conversations",):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
                USING (tenant_id::text = current_setting('app.current_tenant_id', true))
                WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true));
        """)

    # agent_messages doesn't have tenant_id directly — secured via conversation FK
    # but grant access to ims_app
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON agent_conversations TO ims_app;"
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON agent_messages TO ims_app;"
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS agent_conversations_tenant_isolation "
        "ON agent_conversations;"
    )
    op.execute(
        "ALTER TABLE agent_conversations DISABLE ROW LEVEL SECURITY;"
    )
    op.drop_table("agent_messages")
    op.drop_table("agent_conversations")

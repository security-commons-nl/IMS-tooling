"""Add is_default column to TenantUser for default tenant selection

Revision ID: 011_add_tenantuser_is_default
Revises: 010_add_scope_governance_and_risk_treatment
Create Date: 2026-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "011_add_tenantuser_is_default"
down_revision: Union[str, None] = "010_add_scope_governance_and_risk_treatment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_default column
    op.add_column(
        "tenantuser",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # Backfill: set is_default=true for the first membership per user
    # (lowest id per user_id = the earliest membership)
    op.execute("""
        UPDATE tenantuser
        SET is_default = true
        WHERE id IN (
            SELECT DISTINCT ON (user_id) id
            FROM tenantuser
            WHERE is_active = true
            ORDER BY user_id, id ASC
        )
    """)


def downgrade() -> None:
    op.drop_column("tenantuser", "is_default")

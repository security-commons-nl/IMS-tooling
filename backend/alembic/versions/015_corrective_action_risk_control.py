"""Add risk_id and control_id to CorrectiveAction

Allow corrective actions to be linked directly to a Risk or Control,
in addition to Finding/Incident/Issue/Initiative.

Revision ID: 015_ca_risk_control
Revises: 014_appetite_fields
Create Date: 2026-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "015_ca_risk_control"
down_revision: Union[str, None] = "014_appetite_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "correctiveaction",
        sa.Column("risk_id", sa.Integer(), sa.ForeignKey("risk.id"), nullable=True),
    )
    op.add_column(
        "correctiveaction",
        sa.Column("control_id", sa.Integer(), sa.ForeignKey("control.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("correctiveaction", "control_id")
    op.drop_column("correctiveaction", "risk_id")

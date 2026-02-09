"""Relax NOT NULL constraints on description and optional fields

Allow NULL for description fields and optional references so that
create forms don't require every field upfront.

Revision ID: 012_relax_not_null
Revises: 011_add_tenantuser_is_default
Create Date: 2026-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "012_relax_not_null"
down_revision: Union[str, None] = "011_add_tenantuser_is_default"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("control", "description", existing_type=sa.String(), nullable=True)
    op.alter_column("risk", "description", existing_type=sa.String(), nullable=True)
    op.alter_column("risk", "inherent_likelihood", existing_type=sa.String(), nullable=True)
    op.alter_column("risk", "inherent_impact", existing_type=sa.String(), nullable=True)
    op.alter_column("measure", "description", existing_type=sa.String(), nullable=True)
    op.alter_column("incident", "description", existing_type=sa.String(), nullable=True)
    op.alter_column("decision", "decision_maker_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("policy", "content", existing_type=sa.String(), nullable=True)
    op.alter_column("scope", "owner", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.alter_column("scope", "owner", existing_type=sa.String(), nullable=False)
    op.alter_column("policy", "content", existing_type=sa.String(), nullable=False)
    op.alter_column("decision", "decision_maker_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("incident", "description", existing_type=sa.String(), nullable=False)
    op.alter_column("measure", "description", existing_type=sa.String(), nullable=False)
    op.alter_column("risk", "inherent_impact", existing_type=sa.String(), nullable=False)
    op.alter_column("risk", "inherent_likelihood", existing_type=sa.String(), nullable=False)
    op.alter_column("risk", "description", existing_type=sa.String(), nullable=False)
    op.alter_column("control", "description", existing_type=sa.String(), nullable=False)

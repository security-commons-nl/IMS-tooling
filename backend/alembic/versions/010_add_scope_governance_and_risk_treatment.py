"""Add scope governance fields and risk treatment_strategy/policy_principle_id

Adds columns that were in the model but missing from migrations:
- Scope: governance_status, scope_motivation, in_scope, validity_year, established_by_id, established_date
- Risk: treatment_strategy, policy_principle_id

Revision ID: 010_add_scope_governance_and_risk_treatment
Revises: 009_add_entity_relationships
Create Date: 2026-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010_add_scope_governance_and_risk_treatment'
down_revision: Union[str, None] = '009_add_entity_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Scope governance fields
    op.add_column('scope', sa.Column(
        'governance_status',
        sa.Enum('IN_SCOPE', 'OUT_OF_SCOPE', 'UNDER_REVIEW', 'PENDING',
                name='scopegovernancestatus', create_type=False),
        nullable=True
    ))
    op.add_column('scope', sa.Column('scope_motivation', sa.String(), nullable=True))
    op.add_column('scope', sa.Column('in_scope', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('scope', sa.Column('validity_year', sa.Integer(), nullable=True))
    op.add_column('scope', sa.Column(
        'established_by_id', sa.Integer(),
        sa.ForeignKey('user.id'), nullable=True
    ))
    op.add_column('scope', sa.Column('established_date', sa.DateTime(), nullable=True))

    # Risk treatment fields
    op.add_column('risk', sa.Column(
        'treatment_strategy',
        sa.Enum('MITIGATE', 'ACCEPT', 'TRANSFER', 'AVOID',
                name='treatmentstrategy', create_type=False),
        nullable=True
    ))
    op.add_column('risk', sa.Column(
        'policy_principle_id', sa.Integer(),
        sa.ForeignKey('policyprinciple.id'), nullable=True
    ))


def downgrade() -> None:
    op.drop_column('risk', 'policy_principle_id')
    op.drop_column('risk', 'treatment_strategy')
    op.drop_column('scope', 'established_date')
    op.drop_column('scope', 'established_by_id')
    op.drop_column('scope', 'validity_year')
    op.drop_column('scope', 'in_scope')
    op.drop_column('scope', 'scope_motivation')
    op.drop_column('scope', 'governance_status')

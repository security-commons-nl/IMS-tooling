"""Add assessment phase/BIA fields and BIAThreshold table

Revision ID: 007_add_assessment_phase_and_bia
Revises: 006_add_risk_transfer_party
Create Date: 2026-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007_add_assessment_phase_and_bia'
down_revision: Union[str, None] = '006_add_risk_transfer_party'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Assessment workflow fields
    op.add_column('assessment', sa.Column('phase', sa.String(), server_default='Aangevraagd'))
    op.add_column('assessment', sa.Column('methodology', sa.String(), nullable=True))
    op.add_column('assessment', sa.Column('next_assessment_date', sa.DateTime(), nullable=True))

    # BIA snapshot fields
    op.add_column('assessment', sa.Column('bia_cia_label', sa.String(), nullable=True))
    op.add_column('assessment', sa.Column('bia_rto_hours', sa.Integer(), nullable=True))
    op.add_column('assessment', sa.Column('bia_rpo_hours', sa.Integer(), nullable=True))
    op.add_column('assessment', sa.Column('bia_mtpd_hours', sa.Integer(), nullable=True))
    op.add_column('assessment', sa.Column('bia_bcp_required', sa.Boolean(), nullable=True))

    # BIA Threshold configuration table
    op.create_table(
        'biathreshold',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenant.id'), nullable=True),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('classification_level', sa.String(), nullable=False),
        sa.Column('rto_hours', sa.Integer(), nullable=False),
        sa.Column('rpo_hours', sa.Integer(), nullable=False),
        sa.Column('mtpd_hours', sa.Integer(), nullable=False),
        sa.Column('rto_label', sa.String(), nullable=False),
        sa.Column('rpo_label', sa.String(), nullable=False),
        sa.Column('plan_required', sa.Boolean(), nullable=False),
        sa.Column('plan_label', sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('biathreshold')
    for col in ['bia_bcp_required', 'bia_mtpd_hours', 'bia_rpo_hours',
                'bia_rto_hours', 'bia_cia_label', 'next_assessment_date',
                'methodology', 'phase']:
        op.drop_column('assessment', col)

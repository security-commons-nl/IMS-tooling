"""Add missing columns to riskappetite table

Revision ID: 019
Revises: 018
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('riskappetite',
        sa.Column('impact_correlation', sa.Text(), nullable=True))
    op.add_column('riskappetite',
        sa.Column('financial_threshold_value', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('riskappetite', 'financial_threshold_value')
    op.drop_column('riskappetite', 'impact_correlation')

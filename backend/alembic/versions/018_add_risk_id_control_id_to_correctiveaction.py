"""add risk_id and control_id to correctiveaction

Revision ID: 018
Revises: 017_add_stakeholder_model
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa

revision = '018'
down_revision = '017_add_stakeholder_model'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('correctiveaction',
        sa.Column('risk_id', sa.Integer(), sa.ForeignKey('risk.id'), nullable=True))
    op.add_column('correctiveaction',
        sa.Column('control_id', sa.Integer(), sa.ForeignKey('control.id'), nullable=True))


def downgrade():
    op.drop_column('correctiveaction', 'control_id')
    op.drop_column('correctiveaction', 'risk_id')

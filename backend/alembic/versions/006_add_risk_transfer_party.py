"""Add risk transfer_party field (stub - applied manually before migration tracking)

Revision ID: 006_add_risk_transfer_party
Revises: 005_role_simplification
Create Date: 2026-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_add_risk_transfer_party'
down_revision: Union[str, None] = '005_role_simplification'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration was applied manually before migration tracking.
    # Stub file to maintain the Alembic revision chain.
    pass


def downgrade() -> None:
    pass

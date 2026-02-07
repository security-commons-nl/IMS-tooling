"""Fix applicabilitystatement column name

Revision ID: 004_fix_applicabilitystatement_column
Revises: 003_backlog_user_story
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_fix_applicabilitystatement_column'
down_revision: Union[str, None] = '003_backlog_user_story'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename shared_measure_adequate to shared_control_adequate."""
    # This column was missed during the Measure→Control refactoring
    op.execute("""
        ALTER TABLE applicabilitystatement
        RENAME COLUMN shared_measure_adequate TO shared_control_adequate
    """)


def downgrade() -> None:
    """Rename back to shared_measure_adequate."""
    op.execute("""
        ALTER TABLE applicabilitystatement
        RENAME COLUMN shared_control_adequate TO shared_measure_adequate
    """)

"""Remove treatment_strategy — attention_quadrant is single source of truth

Migrates existing treatment_strategy data to attention_quadrant where missing,
then drops the treatment_strategy column from risk and riskscope tables.

Mapping:
- Accepteren  → quadrant ACCEPT
- Reduceren   → quadrant MITIGATE + approach REDUCE
- Overdragen  → quadrant MITIGATE + approach TRANSFER
- Vermijden   → quadrant MITIGATE + approach AVOID

Revision ID: 016_remove_treatment
Revises: 015_ca_risk_control
Create Date: 2026-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "016_remove_treatment"
down_revision: Union[str, None] = "015_ca_risk_control"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Migrate data where treatment_strategy is set but attention_quadrant is null
    # This preserves existing attention_quadrant values (they take precedence)

    conn = op.get_bind()

    # Check if treatment_strategy column exists before migrating
    inspector = sa.inspect(conn)
    risk_columns = [c["name"] for c in inspector.get_columns("risk")]

    if "treatment_strategy" in risk_columns:
        # Accepteren → ACCEPT quadrant
        conn.execute(sa.text("""
            UPDATE risk
            SET attention_quadrant = 'Accepteren'
            WHERE treatment_strategy = 'Accepteren'
              AND attention_quadrant IS NULL
        """))

        # Reduceren → MITIGATE quadrant + REDUCE approach
        conn.execute(sa.text("""
            UPDATE risk
            SET attention_quadrant = 'Mitigeren',
                mitigation_approach = 'Reduceren'
            WHERE treatment_strategy = 'Reduceren'
              AND attention_quadrant IS NULL
        """))

        # Overdragen → MITIGATE quadrant + TRANSFER approach
        conn.execute(sa.text("""
            UPDATE risk
            SET attention_quadrant = 'Mitigeren',
                mitigation_approach = 'Overdragen'
            WHERE treatment_strategy = 'Overdragen'
              AND attention_quadrant IS NULL
        """))

        # Vermijden → MITIGATE quadrant + AVOID approach
        conn.execute(sa.text("""
            UPDATE risk
            SET attention_quadrant = 'Mitigeren',
                mitigation_approach = 'Vermijden'
            WHERE treatment_strategy = 'Vermijden'
              AND attention_quadrant IS NULL
        """))

        # Drop column from risk
        op.drop_column("risk", "treatment_strategy")

    # Same for riskscope table
    riskscope_columns = [c["name"] for c in inspector.get_columns("riskscope")]

    if "treatment_strategy" in riskscope_columns:
        # Migrate riskscope data
        conn.execute(sa.text("""
            UPDATE riskscope
            SET attention_quadrant = 'Accepteren'
            WHERE treatment_strategy = 'Accepteren'
              AND attention_quadrant IS NULL
        """))

        conn.execute(sa.text("""
            UPDATE riskscope
            SET attention_quadrant = 'Mitigeren',
                mitigation_approach = 'Reduceren'
            WHERE treatment_strategy = 'Reduceren'
              AND attention_quadrant IS NULL
        """))

        conn.execute(sa.text("""
            UPDATE riskscope
            SET attention_quadrant = 'Mitigeren',
                mitigation_approach = 'Overdragen'
            WHERE treatment_strategy = 'Overdragen'
              AND attention_quadrant IS NULL
        """))

        conn.execute(sa.text("""
            UPDATE riskscope
            SET attention_quadrant = 'Mitigeren',
                mitigation_approach = 'Vermijden'
            WHERE treatment_strategy = 'Vermijden'
              AND attention_quadrant IS NULL
        """))

        # Drop column from riskscope
        op.drop_column("riskscope", "treatment_strategy")


def downgrade() -> None:
    # Re-add treatment_strategy columns
    op.add_column(
        "risk",
        sa.Column("treatment_strategy", sa.String(), nullable=True),
    )
    op.add_column(
        "riskscope",
        sa.Column("treatment_strategy", sa.String(), nullable=True),
    )

"""Simplify roles: 6+3 roles → 5 unified roles (Three Lines model)

Revision ID: 005_role_simplification
Revises: 004_fix_applicabilitystatement_column
Create Date: 2026-02-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_role_simplification'
down_revision: Union[str, None] = '004_fix_applicabilitystatement_column'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Role mapping: old → new
ROLE_MAPPING = {
    'Admin': 'Beheerder',
    'ProcessOwner': 'Eigenaar',
    'SystemOwner': 'Eigenaar',
    'RiskOwner': 'Eigenaar',
    'Editor': 'Medewerker',
    'Viewer': 'Toezichthouder',
}


def upgrade() -> None:
    # 1. Migrate userscoperole.role values
    for old_role, new_role in ROLE_MAPPING.items():
        op.execute(
            sa.text(
                "UPDATE userscoperole SET role = :new WHERE role = :old"
            ).bindparams(new=new_role, old=old_role)
        )

    # 2. Migrate workflowstate.allowed_roles (JSON text field)
    for old_role, new_role in ROLE_MAPPING.items():
        op.execute(
            sa.text(
                "UPDATE workflowstate SET allowed_roles = REPLACE(allowed_roles, :old, :new) "
                "WHERE allowed_roles IS NOT NULL AND allowed_roles LIKE :pattern"
            ).bindparams(new=new_role, old=old_role, pattern=f'%{old_role}%')
        )

    # 3. Migrate workflowtransition.allowed_roles and approver_roles
    for old_role, new_role in ROLE_MAPPING.items():
        op.execute(
            sa.text(
                "UPDATE workflowtransition SET allowed_roles = REPLACE(allowed_roles, :old, :new) "
                "WHERE allowed_roles IS NOT NULL AND allowed_roles LIKE :pattern"
            ).bindparams(new=new_role, old=old_role, pattern=f'%{old_role}%')
        )
        op.execute(
            sa.text(
                "UPDATE workflowtransition SET approver_roles = REPLACE(approver_roles, :old, :new) "
                "WHERE approver_roles IS NOT NULL AND approver_roles LIKE :pattern"
            ).bindparams(new=new_role, old=old_role, pattern=f'%{old_role}%')
        )

    # 4. Migrate workflowtransition.required_role
    for old_role, new_role in ROLE_MAPPING.items():
        op.execute(
            sa.text(
                "UPDATE workflowtransition SET required_role = :new WHERE required_role = :old"
            ).bindparams(new=new_role, old=old_role)
        )

    # 5. Drop tenantuser.role column
    op.drop_column('tenantuser', 'role')


def downgrade() -> None:
    # Re-add tenantuser.role column with default
    op.add_column(
        'tenantuser',
        sa.Column('role', sa.String(), server_default='Member', nullable=True)
    )

    # Reverse role mapping
    REVERSE_MAPPING = {
        'Beheerder': 'Admin',
        'Eigenaar': 'ProcessOwner',
        'Medewerker': 'Editor',
        'Toezichthouder': 'Viewer',
        'Coordinator': 'Admin',
    }

    for new_role, old_role in REVERSE_MAPPING.items():
        op.execute(
            sa.text(
                "UPDATE userscoperole SET role = :old WHERE role = :new"
            ).bindparams(old=old_role, new=new_role)
        )

    for new_role, old_role in REVERSE_MAPPING.items():
        op.execute(
            sa.text(
                "UPDATE workflowtransition SET required_role = :old WHERE required_role = :new"
            ).bindparams(old=old_role, new=new_role)
        )

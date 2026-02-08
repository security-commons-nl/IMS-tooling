"""Add cross-domain entity relationships

Adds 9 new relationships based on ISO 27001, ISO 22301, and ISO 27701 requirements:
- Risk.processing_activity_id (ISO 27701)
- Assessment.processing_activity_id (AVG Art. 35)
- Decision.management_review_id (ISO 27001 9.3.3)
- Exception.risk_id (ISO 27001 risk acceptance)
- ContinuityTest.assessment_id (ISO 22301 8.5)
- Incident.continuity_plan_id (ISO 22301 8.4.4)
- Incident.processing_activity_id (AVG Art. 33/34)
- IncidentControlLink M2M table (root cause analysis)
- InitiativeObjectiveLink M2M table (ISO 27001 6.2 + 10.2)

Revision ID: 009_add_entity_relationships
Revises: 008_add_organization_profile
Create Date: 2026-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009_add_entity_relationships'
down_revision: Union[str, None] = '008_add_organization_profile'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- FK columns on existing tables ---

    # 1. Risk -> ProcessingActivity (ISO 27701 / AVG)
    op.add_column('risk', sa.Column(
        'processing_activity_id', sa.Integer(),
        sa.ForeignKey('processingactivity.id'), nullable=True
    ))

    # 2. Assessment -> ProcessingActivity (AVG Art. 35 DPIA)
    op.add_column('assessment', sa.Column(
        'processing_activity_id', sa.Integer(),
        sa.ForeignKey('processingactivity.id'), nullable=True
    ))

    # 3. Decision -> ManagementReview (ISO 27001 9.3.3)
    op.add_column('decision', sa.Column(
        'management_review_id', sa.Integer(),
        sa.ForeignKey('managementreview.id'), nullable=True
    ))

    # 4. Exception -> Risk (ISO 27001 risk acceptance)
    op.add_column('exception', sa.Column(
        'risk_id', sa.Integer(),
        sa.ForeignKey('risk.id'), nullable=True
    ))

    # 5. ContinuityTest -> Assessment (ISO 22301 8.5 + 10.1)
    op.add_column('continuitytest', sa.Column(
        'assessment_id', sa.Integer(),
        sa.ForeignKey('assessment.id'), nullable=True
    ))

    # 6. Incident -> ContinuityPlan (ISO 22301 8.4.4)
    op.add_column('incident', sa.Column(
        'continuity_plan_id', sa.Integer(),
        sa.ForeignKey('continuityplan.id'), nullable=True
    ))

    # 7. Incident -> ProcessingActivity (AVG Art. 33/34)
    op.add_column('incident', sa.Column(
        'processing_activity_id', sa.Integer(),
        sa.ForeignKey('processingactivity.id'), nullable=True
    ))

    # --- New M2M tables ---

    # 8. IncidentControlLink (root cause analysis)
    op.create_table(
        'incidentcontrollink',
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incident.id'), primary_key=True),
        sa.Column('control_id', sa.Integer(), sa.ForeignKey('control.id'), primary_key=True),
        sa.Column('failure_description', sa.String(), nullable=True),
        sa.Column('contributed_to_incident', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # 9. InitiativeObjectiveLink (ISO 27001 6.2 + 10.2)
    op.create_table(
        'initiativeobjectivelink',
        sa.Column('initiative_id', sa.Integer(), sa.ForeignKey('initiative.id'), primary_key=True),
        sa.Column('objective_id', sa.Integer(), sa.ForeignKey('objective.id'), primary_key=True),
        sa.Column('contribution_description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    # Drop M2M tables
    op.drop_table('initiativeobjectivelink')
    op.drop_table('incidentcontrollink')

    # Drop FK columns
    op.drop_column('incident', 'processing_activity_id')
    op.drop_column('incident', 'continuity_plan_id')
    op.drop_column('continuitytest', 'assessment_id')
    op.drop_column('exception', 'risk_id')
    op.drop_column('decision', 'management_review_id')
    op.drop_column('assessment', 'processing_activity_id')
    op.drop_column('risk', 'processing_activity_id')

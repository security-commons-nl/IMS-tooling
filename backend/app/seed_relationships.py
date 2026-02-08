"""
Seed Relationship Data
Idempotent script that creates missing link-table records for the relationship graph.
Creates Controls and links them to Risks and Measures.

Usage:
    python -m app.seed_relationships
"""
import asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_engine
from app.models.core_models import (
    Risk,
    Control,
    Measure,
    Scope,
    ControlRiskLink,
    ControlMeasureLink,
)


async def seed_relationships():
    """Create Controls + link records if they don't exist yet."""
    from sqlalchemy.ext.asyncio import AsyncSession as AS

    async with AS(async_engine, expire_on_commit=False) as session:
        # Load existing entities for tenant 1
        risks = (await session.execute(select(Risk).where(Risk.tenant_id == 1))).scalars().all()
        measures = (await session.execute(select(Measure).where(Measure.tenant_id == 1))).scalars().all()
        scopes = (await session.execute(select(Scope).where(Scope.tenant_id == 1))).scalars().all()
        existing_controls = (await session.execute(select(Control).where(Control.tenant_id == 1))).scalars().all()

        if not risks or not measures:
            print("No risks or measures found — run seed_data first.")
            return

        # Get process-level scopes for assigning controls
        process_scopes = [s for s in scopes if s.type and s.type.value == "process"]
        if not process_scopes:
            process_scopes = scopes[:1]  # fallback

        # --- Create Controls if none exist ---
        if not existing_controls:
            print("Creating Controls...")
            controls_data = [
                {
                    "title": "MFA voor alle gebruikers",
                    "description": "Multi-factor authenticatie actief voor alle accounts via Azure AD",
                    "scope_idx": 0,
                },
                {
                    "title": "Dagelijkse backup verificatie",
                    "description": "Automatische controle dat backups succesvol zijn uitgevoerd",
                    "scope_idx": 1 % len(process_scopes),
                },
                {
                    "title": "Kwartaalrapportage datalekken",
                    "description": "Overzicht van datalekmeldingen en opvolging per kwartaal",
                    "scope_idx": 2 % len(process_scopes),
                },
                {
                    "title": "Patchmanagement scan",
                    "description": "Wekelijkse vulnerability scan en patch-compliance rapportage",
                    "scope_idx": 0,
                },
            ]
            controls = []
            for cd in controls_data:
                control = Control(
                    tenant_id=1,
                    title=cd["title"],
                    description=cd["description"],
                    scope_id=process_scopes[cd["scope_idx"]].id,
                    is_active=True,
                )
                session.add(control)
                controls.append(control)
            await session.flush()
            print(f"  Created {len(controls)} controls")
        else:
            controls = list(existing_controls)
            print(f"Controls already exist ({len(controls)}), skipping creation")

        # --- Create ControlRiskLink records ---
        existing_cr = (await session.execute(select(ControlRiskLink))).scalars().all()
        if not existing_cr:
            print("Creating ControlRiskLink records...")
            # Link controls to risks (each control mitigates 1-2 risks)
            links = []
            for i, control in enumerate(controls):
                # Each control mitigates the risk at the same index (wrap around)
                if i < len(risks):
                    link = ControlRiskLink(
                        control_id=control.id,
                        risk_id=risks[i].id,
                        mitigation_percent=70 + (i * 5) % 30,
                    )
                    session.add(link)
                    links.append(link)
                # Second risk link for first two controls
                if i < 2 and (i + 1) < len(risks):
                    link2 = ControlRiskLink(
                        control_id=control.id,
                        risk_id=risks[i + 1].id,
                        mitigation_percent=40 + (i * 10),
                    )
                    session.add(link2)
                    links.append(link2)
            await session.flush()
            print(f"  Created {len(links)} control-risk links")
        else:
            print(f"ControlRiskLinks already exist ({len(existing_cr)}), skipping")

        # --- Create ControlMeasureLink records ---
        existing_cm = (await session.execute(select(ControlMeasureLink))).scalars().all()
        if not existing_cm and measures:
            print("Creating ControlMeasureLink records...")
            cm_links = []
            for i, control in enumerate(controls):
                if i < len(measures):
                    cm = ControlMeasureLink(
                        control_id=control.id,
                        measure_id=measures[i].id,
                        coverage_percentage=80 + (i * 5) % 20,
                    )
                    session.add(cm)
                    cm_links.append(cm)
            await session.flush()
            print(f"  Created {len(cm_links)} control-measure links")
        else:
            print(f"ControlMeasureLinks already exist ({len(existing_cm)}), skipping")

        await session.commit()
        print("Done! Relationship seed complete.")

        # Summary
        cr_count = len((await session.execute(select(ControlRiskLink))).scalars().all())
        cm_count = len((await session.execute(select(ControlMeasureLink))).scalars().all())
        ctrl_count = len((await session.execute(select(Control).where(Control.tenant_id == 1))).scalars().all())
        print(f"\nSummary: {ctrl_count} controls, {cr_count} control-risk links, {cm_count} control-measure links")


if __name__ == "__main__":
    asyncio.run(seed_relationships())

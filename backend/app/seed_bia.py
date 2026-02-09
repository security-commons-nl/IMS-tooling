"""
Seed BIA Questions and Thresholds only.
Idempotent: checks for existing data before inserting.

Run: python -m app.seed_bia
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from sqlmodel import SQLModel

from app.core.config import settings
from app.models.core_models import (
    AssessmentQuestion, QuestionType, BIAThreshold,
)


async def seed_bia():
    """Seed BIA thresholds and questions (idempotent)."""
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # =================================================================
        # BIA THRESHOLDS
        # =================================================================
        existing_thresholds = (
            await session.execute(
                select(func.count()).select_from(BIAThreshold)
            )
        ).scalar_one()

        if existing_thresholds == 0:
            thresholds = [
                BIAThreshold(
                    tenant_id=None, score=1, label="Laag",
                    classification_level="Public",
                    rto_hours=168, rpo_hours=24, mtpd_hours=336,
                    rto_label="< 1 week", rpo_label="< 24 uur",
                    plan_required=False, plan_label="Nee",
                ),
                BIAThreshold(
                    tenant_id=None, score=2, label="Midden",
                    classification_level="Internal",
                    rto_hours=24, rpo_hours=4, mtpd_hours=72,
                    rto_label="< 24 uur", rpo_label="< 4 uur",
                    plan_required=True, plan_label="Basis BCP",
                ),
                BIAThreshold(
                    tenant_id=None, score=3, label="Hoog",
                    classification_level="Confidential",
                    rto_hours=4, rpo_hours=1, mtpd_hours=24,
                    rto_label="< 4 uur", rpo_label="< 1 uur",
                    plan_required=True, plan_label="Uitgebreid BCP",
                ),
                BIAThreshold(
                    tenant_id=None, score=4, label="Kritiek",
                    classification_level="Secret",
                    rto_hours=0, rpo_hours=0, mtpd_hours=4,
                    rto_label="< 15 min", rpo_label="0 (geen verlies)",
                    plan_required=True, plan_label="Full DR Plan",
                ),
            ]
            for t in thresholds:
                session.add(t)
            await session.commit()
            print(f"Inserted {len(thresholds)} BIA thresholds")
        else:
            print(f"BIA thresholds already exist ({existing_thresholds} rows), skipping")

        # =================================================================
        # BIA QUESTIONS
        # =================================================================
        existing_questions = (
            await session.execute(
                select(func.count()).select_from(AssessmentQuestion).where(
                    AssessmentQuestion.code.like("BIA-Q%")
                )
            )
        ).scalar_one()

        if existing_questions == 0:
            questions_data = [
                {"code": "BIA-Q1", "question_text": "Bevat dit proces/systeem persoonsgegevens of geheimhoudingsgevoelige informatie?",
                 "category": "BIA-A", "section": "Vertrouwelijkheid", "order": 1,
                 "guidance": "Denk aan BSN, medische gegevens, financiele data, bedrijfsgeheimen."},
                {"code": "BIA-Q2", "question_text": "Wat is de reputatieschade of boeterisico als deze data op straat ligt?",
                 "category": "BIA-A", "section": "Vertrouwelijkheid", "order": 2,
                 "guidance": "1=minimaal, 2=beperkt, 3=significant, 4=existentieel (AVG-boete, mediacrisis)."},
                {"code": "BIA-Q3", "question_text": "Hoe cruciaal is het dat de data 100% accuraat is?",
                 "category": "BIA-A", "section": "Integriteit", "order": 3,
                 "guidance": "Denk aan financiele transacties, medische dossiers, juridische besluiten."},
                {"code": "BIA-Q4", "question_text": "Wat is de impact als een onbevoegd persoon data ongemerkt wijzigt?",
                 "category": "BIA-A", "section": "Integriteit", "order": 4,
                 "guidance": "1=minimaal, 2=beperkt, 3=significant (verkeerde besluiten), 4=catastrofaal."},
                {"code": "BIA-Q5", "question_text": "Wat is de directe schade per uur/dag dat dit proces stilstaat?",
                 "category": "BIA-B", "section": "Beschikbaarheid", "order": 5,
                 "guidance": "1=verwaarloosbaar, 2=beperkt, 3=significant omzetverlies, 4=onacceptabel."},
                {"code": "BIA-Q6", "question_text": "Zijn er SLA's of wetten die een maximale downtime dicteren?",
                 "category": "BIA-B", "section": "Beschikbaarheid", "order": 6,
                 "guidance": "1=geen afspraken, 2=interne SLA, 3=externe SLA, 4=wettelijke verplichting."},
                {"code": "BIA-Q7", "question_text": "Hoeveel andere bedrijfsprocessen vallen stil als dit systeem stopt?",
                 "category": "BIA-B", "section": "Beschikbaarheid", "order": 7,
                 "guidance": "1=geen, 2=1-2 processen, 3=3-5 processen, 4=kritieke keten stopt."},
                {"code": "BIA-Q8", "question_text": "Hoe snel merken klanten dat de dienstverlening is onderbroken?",
                 "category": "BIA-B", "section": "Beschikbaarheid", "order": 8,
                 "guidance": "1=niet, 2=na dagen, 3=binnen uren, 4=direct."},
                {"code": "BIA-Q9", "question_text": "Is verloren data handmatig te herstellen?",
                 "category": "BIA-C", "section": "Dataverlies", "order": 9,
                 "guidance": "1=volledig herstelbaar, 2=deels herstelbaar, 3=moeilijk, 4=onmogelijk."},
                {"code": "BIA-Q10", "question_text": "Hoeveel nieuwe data wordt er per uur geproduceerd?",
                 "category": "BIA-C", "section": "Dataverlies", "order": 10,
                 "guidance": "1=weinig, 2=matig, 3=veel, 4=continu (real-time transacties)."},
                {"code": "BIA-Q11", "question_text": "Is er een kritiek herstelmoment waarop herstel binnen minuten essentieel is?",
                 "category": "BIA-C", "section": "RTO modifier", "order": 11,
                 "guidance": "1=nee, 2=binnen dagen, 3=binnen uren, 4=binnen minuten (RTO modifier)."},
                {"code": "BIA-Q12", "question_text": "Is er een workaround beschikbaar tijdens uitval?",
                 "category": "BIA-C", "section": "RTO modifier", "order": 12,
                 "guidance": "1=volledige workaround, 2=beperkte workaround, 3=minimale workaround, 4=geen workaround (RTO modifier)."},
            ]

            for q in questions_data:
                session.add(AssessmentQuestion(
                    tenant_id=None,
                    question_type=QuestionType.SCALE_1_4,
                    weight=1.0,
                    is_active=True,
                    **q,
                ))
            await session.commit()
            print(f"Inserted {len(questions_data)} BIA questions")
        else:
            print(f"BIA questions already exist ({existing_questions} rows), skipping")

    await engine.dispose()
    print("BIA seed complete.")


if __name__ == "__main__":
    asyncio.run(seed_bia())

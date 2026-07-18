"""Behavior tests for report-category LFU-Aging ordering."""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import BaseModel, CalcReportCategory, User
from app.service import calc_report_category_service


def test_category_access_ages_automatic_counts_before_increment(monkeypatch) -> None:
    """Unpinned visible counts should decay by elapsed epochs before access."""

    async def run_test() -> None:
        """Create category states, record access, and verify persisted counters."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as connection:
                await connection.run_sync(BaseModel.metadata.create_all)
            session_factory = async_sessionmaker(engine, expire_on_commit=False)
            async with session_factory() as session:
                user = User(
                    username="lfu-user",
                    password="hash",
                    salt="salt",
                    roles=["regular"],
                )
                session.add(user)
                await session.flush()
                selected = CalcReportCategory(
                    userId=user.id,
                    name="selected",
                    frequencyCount=16,
                    agingEpoch=8,
                )
                automatic = CalcReportCategory(
                    userId=user.id,
                    name="automatic",
                    frequencyCount=8,
                    agingEpoch=8,
                )
                pinned = CalcReportCategory(
                    userId=user.id,
                    name="pinned",
                    frequencyCount=32,
                    agingEpoch=8,
                    isPinned=True,
                )
                session.add_all([selected, automatic, pinned])
                await session.commit()
                monkeypatch.setattr(
                    calc_report_category_service,
                    "_current_aging_epoch",
                    lambda: 10,
                )

                await calc_report_category_service.record_category_access(
                    user.id, selected.oid, session
                )

                assert selected.frequencyCount == 5
                assert automatic.frequencyCount == 2
                assert pinned.frequencyCount == 32
                assert selected.agingEpoch == 10
                assert automatic.agingEpoch == 10
                assert pinned.agingEpoch == 8
        finally:
            await engine.dispose()

    asyncio.run(run_test())

import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.controller.calc.calc_dto import CalcReportInstanceSaveReqDTO
from app.db.models import (
    BaseModel,
    CalcReport,
    CalcReportCategory,
    CalcReportInstanceCategory,
)
from app.service import calc_report_instance_service


def test_save_calc_report_instance_copies_cached_result_to_permanent_dir(
    tmp_path: Path, monkeypatch
):
    """保存计算实例时应将临时结果复制到永久实例目录。"""

    async def run_test() -> None:
        monkeypatch.chdir(tmp_path)
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(BaseModel.metadata.create_all)

            session_factory = async_sessionmaker(engine, expire_on_commit=False)
            async with session_factory() as session:
                report_category = CalcReportCategory(
                    userId=1, name="reports", order=1, total=0
                )
                instance_category = CalcReportInstanceCategory(
                    userId=1, name="instances", order=1, total=0
                )
                session.add_all([report_category, instance_category])
                await session.commit()
                await session.refresh(report_category)
                await session.refresh(instance_category)

                report = CalcReport(
                    userId=1,
                    categoryId=report_category.id,
                    name="demo",
                    description="demo report",
                )
                session.add(report)
                await session.commit()
                await session.refresh(report)

                cache_dir = tmp_path / "data" / "public" / "calcs" / "1" / "exec-1"
                images_dir = cache_dir / "images"
                images_dir.mkdir(parents=True)
                (cache_dir / "result.html").write_text(
                    '<img src="images/image_1.png">', encoding="utf-8"
                )
                (images_dir / "image_1.png").write_bytes(b"image")

                data = CalcReportInstanceSaveReqDTO(
                    name="instance-a",
                    description="saved result",
                    categoryId=instance_category.id,
                    reportOid=report.oid,
                    defaults={"参数": {"a": 1}},
                    resultPath="public/calcs/1/exec-1/result.html",
                )

                result = await calc_report_instance_service.save_calc_report_instance(
                    1, data, session
                )

                assert result.resultPath.startswith("public/calc-instances/1/")
                saved_html = tmp_path / "data" / result.resultPath
                assert saved_html.exists()
                assert (saved_html.parent / "images" / "image_1.png").exists()
                assert result.defaults == {"参数": {"a": 1}}
                assert result.reportOid == report.oid
                assert instance_category.total == 1
        finally:
            await engine.dispose()

    asyncio.run(run_test())

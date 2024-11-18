from datetime import date, datetime, timedelta

from pydantic import TypeAdapter
from sqlalchemy import func, select, sql
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import PageView

from .schemas import DailyPlatformStats, PlatformStats


async def get_platform_stats(db_session: AsyncSession) -> PlatformStats:
    query = sql.select(
        (
            sql.select(PageView.url)
            .group_by(PageView.url)
            .order_by(func.count(PageView.id).desc())
            .limit(1)
            .subquery()
        ),
        (
            sql.select(func.count(func.distinct(PageView.user_id)))
            .where(PageView.created_at >= datetime.now() - timedelta(days=30))
            .subquery()
        ),
    )
    cursor_result = await db_session.execute(query)
    most_popular_page, monthly_active_users = cursor_result.tuples().one()
    return PlatformStats(
        most_popular_page=most_popular_page,
        monthly_active_users_count=monthly_active_users,
        current_online_users_count=1,
    )


async def get_daily_platform_stats_distribution(
    db_session: AsyncSession,
    start_date: date,
    end_date: date,
    limit: int = 50,
    offset: int = 0,
) -> list[DailyPlatformStats]:
    query = (
        select(
            func.date(PageView.created_at).label("day"),
            func.count(PageView.id).label("page_views"),
            func.count(func.distinct(PageView.user_id)).label("active_users"),
        )
        .where(PageView.created_at.between(start_date, end_date))
        .group_by(func.date(PageView.created_at))
        .order_by(func.date(PageView.created_at))
        .limit(limit)
        .offset(offset)
    )

    cursor_result = await db_session.execute(query)
    ta = TypeAdapter(list[DailyPlatformStats])
    return ta.validate_python(cursor_result.mappings().all())

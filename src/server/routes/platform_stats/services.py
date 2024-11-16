from datetime import datetime, timedelta

from sqlalchemy import func, sql
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import PageView

from .schemas import PlatformStats


async def get_platform_stats(session: AsyncSession) -> PlatformStats:
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
    cursor_result = await session.execute(query)
    most_popular_page, monthly_active_users = cursor_result.tuples().one()
    return PlatformStats(
        most_popular_page=most_popular_page,
        monthly_active_users_count=monthly_active_users,
        current_online_users_count=0,
    )

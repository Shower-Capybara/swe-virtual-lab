from datetime import date

from pydantic import BaseModel


class PlatformStats(BaseModel):
    most_popular_page: str
    monthly_active_users_count: int
    current_online_users_count: int


class DailyPlatformStats(BaseModel):
    day: date
    page_views: int
    active_users: int

"""
Statistics service — prepares data for charts.
Only produces data; does not render charts.
"""
from app.domain.repositories.usage_repository import UsageRepository


class StatisticsService:
    """Provides statistics data for chart rendering."""

    def __init__(self, usage_repo: UsageRepository):
        self._usage_repo = usage_repo

    def get_user_stats(self, filter_mode: str = "all") -> list:
        """Get user statistics for bar chart."""
        return self._usage_repo.get_user_stats(filter_mode)

    def get_hourly_stats(self) -> list:
        """Get hourly usage data for heatmap."""
        return self._usage_repo.get_hourly_stats()

    def get_daily_stats(self, days: int = 30) -> list:
        """Get daily usage data for trend chart."""
        return self._usage_repo.get_daily_stats(days)

    def get_user_distribution(self, filter_mode: str = "all") -> list:
        """Get user distribution data for pie chart."""
        return self._usage_repo.get_user_distribution(filter_mode)

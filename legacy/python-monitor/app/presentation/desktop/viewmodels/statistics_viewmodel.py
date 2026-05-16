"""
Statistics ViewModel — bridges StatisticsService and StatisticsFrame.
Manages chart type selection and data fetching.
"""


class StatisticsViewModel:
    """Provides chart data and chart-type state for StatisticsFrame."""

    CHART_TYPES = ["柱状图", "热力图", "趋势图", "饼图"]

    def __init__(self, statistics_service):
        self._svc = statistics_service
        self.chart_type = "柱状图"

    def get_chart_data(self) -> dict:
        """Get data for the currently selected chart type.
        Returns dict with keys: chart_type, data, extra (e.g. days, filter_mode).
        """
        ct = self.chart_type
        if ct == "柱状图":
            return {"chart_type": ct, "data": self._svc.get_user_stats("all")}
        elif ct == "热力图":
            return {"chart_type": ct, "data": self._svc.get_hourly_stats(), "days": 30}
        elif ct == "趋势图":
            return {"chart_type": ct, "data": self._svc.get_daily_stats(30), "days": 30}
        elif ct == "饼图":
            return {"chart_type": ct, "data": self._svc.get_user_distribution("all"), "filter_mode": "all"}
        return {"chart_type": ct, "data": []}

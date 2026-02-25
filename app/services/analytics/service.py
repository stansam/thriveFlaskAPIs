from datetime import timezone, datetime
from typing import Dict, Any

from app.repository import repositories
from app.dto.analytics.schemas import TrackEventDTO, ReportFilterDTO
from app.services.analytics.utils import group_report_by_date

class AnalyticsService:
    """
    AnalyticsService manages asynchronous event tracking, resolving high throughput
    events chronologically into the structured AnalyticsMetrics relational store explicitly.
    """

    def __init__(self):
        self.analytics_repo = repositories.analytics

    def track_event(self, payload: TrackEventDTO) -> None:
        """
        Ingests a loose runtime metric event incrementing absolute hit counts 
        mapped tightly to the active date bounds logically grouping values avoiding row bloat natively.
        """
        current_date = datetime.now(timezone.utc).date()
        
        self.analytics_repo.increment_metric_counter(
            metric_name=payload.metric_name,
            date_dimension=current_date,
            category=payload.category,
            dimension_key=payload.dimension_key,
            value=payload.value
        )

    def generate_dashboard_report(self, filters: ReportFilterDTO) -> Dict[str, Any]:
        """
        Scans historic timeseries intervals explicitly grouping chronological vectors
        parsing explicit charting payloads accurately rendering React components easily.
        """
        dataset = self.analytics_repo.get_metrics_in_range(
            start_date=filters.start_date,
            end_date=filters.end_date,
            metric_names=filters.metric_names
        )
        
        return {
            "start_date": filters.start_date.isoformat(),
            "end_date": filters.end_date.isoformat(),
            "total_records": len(dataset),
            "data": group_report_by_date(dataset)
        }

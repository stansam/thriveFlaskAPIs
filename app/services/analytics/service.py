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
        
        # Check active dimensional grouping map (e.g. today's hits for metric_name X)
        existing_metric = self.analytics_repo.model.query.filter_by(
            metric_name=payload.metric_name,
            date_dimension=current_date,
            dimension_key=payload.dimension_key
        ).first()

        if existing_metric:
            updates = {
                "value": existing_metric.value + payload.value,
                "count": existing_metric.count + 1
            }
            if payload.category:
                updates["category"] = payload.category
            self.analytics_repo.update(existing_metric.id, updates, commit=True)
        else:
            self.analytics_repo.create({
                "metric_name": payload.metric_name,
                "date_dimension": current_date,
                "value": payload.value,
                "count": 1,
                "category": payload.category,
                "dimension_key": payload.dimension_key
            }, commit=True)

    def generate_dashboard_report(self, filters: ReportFilterDTO) -> Dict[str, Any]:
        """
        Scans historic timeseries intervals explicitly grouping chronological vectors
        parsing explicit charting payloads accurately rendering React components easily.
        """
        query = self.analytics_repo.model.query.filter(
            self.analytics_repo.model.date_dimension >= filters.start_date,
            self.analytics_repo.model.date_dimension <= filters.end_date
        )

        if filters.metric_names:
            query = query.filter(self.analytics_repo.model.metric_name.in_(filters.metric_names))
            
        dataset = query.order_by(self.analytics_repo.model.date_dimension).all()
        
        return {
            "start_date": filters.start_date.isoformat(),
            "end_date": filters.end_date.isoformat(),
            "total_records": len(dataset),
            "data": group_report_by_date(dataset)
        }

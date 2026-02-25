from typing import List
from datetime import date
from sqlalchemy import func
from app.extensions import db
from app.models.analytics import AnalyticsMetric
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.analytics.utils import normalize_metric_name, normalize_date

class AnalyticsRepository(BaseRepository[AnalyticsMetric]):
    """
    AnalyticsRepository responsible for scaling massive telemetry and usage counts
    across the core architectures utilizing DB-native grouping metrics securely.
    """

    def __init__(self):
        super().__init__(AnalyticsMetric)

    @handle_db_exceptions
    def increment_metric_counter(self, metric_name: str, date_dimension: date, category: str = "general") -> AnalyticsMetric:
        """
        Atomically UPSERTS an interaction counter mapping against a specific dimensional date. 
        If the row for `metric:date:category` exists, increments count, otherwise creates it.
        """
        cln_name = normalize_metric_name(metric_name)
        cln_date = normalize_date(date_dimension)
        
        metric = self.model.query.filter_by(
            metric_name=cln_name,
            date_dimension=cln_date,
            category=category
        ).with_for_update().first() # Lock the row to prevent race conditions during the +=1 increment
        
        if metric:
            metric.count += 1
        else:
            metric = self.model(
                metric_name=cln_name,
                date_dimension=cln_date,
                category=category,
                count=1
            )
            db.session.add(metric)
            
        db.session.commit()
        return metric

    @handle_db_exceptions
    def aggregate_metrics_by_date(self, metric_name: str, start_date: date, end_date: date) -> List[dict]:
        """
        Leans into SQLAlchemy `func.sum` aggregating chronological metrics spanning bounds 
        into standard discrete JSON-compatible series lists for Admin dashboards.
        """
        cln_name = normalize_metric_name(metric_name)
        
        results = db.session.query(
            self.model.date_dimension.label('date'),
            func.sum(self.model.count).label('total_count')
        ).filter(
            self.model.metric_name == cln_name,
            self.model.date_dimension >= start_date,
            self.model.date_dimension <= end_date
        ).group_by(
            self.model.date_dimension
        ).order_by(
            self.model.date.asc()
        ).all()
        
        # Format as easily consumable JSON dictionaries
        return [
            {
                "date": res.date.isoformat(),
                "total_count": int(res.total_count) if res.total_count else 0
            }
            for res in results
        ]

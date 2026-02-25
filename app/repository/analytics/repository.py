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
    def increment_metric_counter(self, metric_name: str, date_dimension: date, category: str = "general", dimension_key: str = None, value: float = 0.0) -> AnalyticsMetric:
        """
        Atomically UPSERTS an interaction counter mapping against a specific dimensional date. 
        If the row for `metric:date:category:dimension_key` exists, increments count, otherwise creates it.
        """
        cln_name = normalize_metric_name(metric_name)
        cln_date = normalize_date(date_dimension)
        
        metric = self.model.query.filter_by(
            metric_name=cln_name,
            date_dimension=cln_date,
            dimension_key=dimension_key,
            category=category
        ).with_for_update().first() # Lock the row to prevent race conditions during the +=1 increment
        
        if metric:
            metric.count += 1
            if value is not None:
                metric.value = (metric.value or 0) + value
        else:
            metric = self.model(
                metric_name=cln_name,
                date_dimension=cln_date,
                category=category,
                dimension_key=dimension_key,
                count=1,
                value=value
            )
            db.session.add(metric)
            
        db.session.commit()
        return metric

    @handle_db_exceptions
    def get_metrics_in_range(self, start_date: date, end_date: date, metric_names: List[str] = None) -> List[AnalyticsMetric]:
        query = self.model.query.filter(
            self.model.date_dimension >= start_date,
            self.model.date_dimension <= end_date
        )

        if metric_names:
            query = query.filter(self.model.metric_name.in_(metric_names))
            
        return query.order_by(self.model.date_dimension).all()

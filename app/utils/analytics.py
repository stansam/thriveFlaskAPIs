from datetime import date
from flask import current_app
from app.extensions import db
from app.models.analytics import AnalyticsMetric
import logging

logger = logging.getLogger(__name__)

def track_metric(
    metric_name: str,
    value: float = 1.0,
    category: str = None,
    dimension_key: str = None
):
    """
    Tracks an analytics metric. Aggregates values for the same metric/day/dimensions.
    
    Args:
        metric_name (str): The name of the metric (e.g., 'login_success').
        value (float): The value to add (default 1.0 for counts).
        category (str, optional): Category for grouping.
        dimension_key (str, optional): Specific dimension (e.g., 'Google', 'Email').
    """
    try:
        today = date.today()
        
        # Check if metric exists for today with same dimensions
        # We use a select for update if possible, or just standard query
        # Since this might be high volume, ideally this is async or batched, 
        # but for direct DB implementation:
        
        metric = db.session.query(AnalyticsMetric).filter_by(
            metric_name=metric_name,
            date_dimension=today,
            category=category,
            dimension_key=dimension_key
        ).first()
        
        if metric:
            metric.value += value
            metric.count += 1
        else:
            metric = AnalyticsMetric(
                metric_name=metric_name,
                date_dimension=today,
                value=value,
                count=1,
                category=category,
                dimension_key=dimension_key
            )
            db.session.add(metric)
            
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Failed to track metric {metric_name}: {e}")
        db.session.rollback()

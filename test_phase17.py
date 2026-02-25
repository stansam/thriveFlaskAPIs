from datetime import date
from app.services.analytics.service import AnalyticsService
from app.services.audit.service import AuditService
from app.dto.analytics.schemas import TrackEventDTO, ReportFilterDTO
from app.dto.audit.schemas import LogActionDTO
from app.models.enums import AuditAction, EntityType

print("Phase 17 Imports successful!")
svc1 = AnalyticsService()
svc2 = AuditService()

dto1 = TrackEventDTO(metric_name="PAGE_VIEW", value=1.0)
dto2 = ReportFilterDTO(start_date=date(2023, 1, 1), end_date=date(2023, 12, 31))
dto3 = LogActionDTO(action=AuditAction.CREATE, entity_type=EntityType.USER, entity_id="usr_123")

print("Phase 17 Instantiations successful! DTOs constructed properly.")

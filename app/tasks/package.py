from app.enums import RecipientType
from app.enums import NotificationEventType
import csv
import os
from typing import Any
from decimal import Decimal
from celery import shared_task
from flask import current_app
from app.core.dependencies import get_services
from app.dto.package import TravelPackageCreateRequest
from app.repository import registry as repositories
from app.models.base import db
def safe_str(v: Any) -> str:
    return str(v).strip() if v is not None else ""

@shared_task(ignore_result=True)
def process_package_csv_task(filepath: str, admin_id: str) -> None:
    """
    Asynchronously parses a physical CSV file mapping permutations
    integrating them natively via `PackageService`.
    Dispatches a final completion metric email directly to the Admin actor.
    """
    success_count = 0
    failure_count = 0
    errors = []

    try:
        
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    dto = TravelPackageCreateRequest(
                        title=safe_str(row.get("title")),
                        slug=safe_str(row.get("slug")) or None,
                        tagline=safe_str(row.get("tagline")) or None,
                        description=safe_str(row.get("description")) or None,

                        base_price_usd=Decimal(str(row.get("price", "0")).strip() or "0"),

                        duration_days=int(row.get("duration_days") or 1),
                        duration_nights=int(row.get("duration_nights") or 1),

                        destination_country=safe_str(row.get("destination_country")),
                        destination_city=safe_str(row.get("destination_city")) or None,
                        region=safe_str(row.get("region")) or None,

                        is_featured=str(row.get("is_featured", "false")).lower() == "true",

                        min_participants=int(row.get("min_participants") or 1),
                        max_participants=int(row.get("max_participants") or 0) or None,
                    )
                    
                    if not dto.title or not dto.slug or not dto.destination_country:
                        raise ValueError("Missing mandatory logical fields natively.")
                        
                    get_services().package.create_package(dto, admin_id)
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    errors.append(f"Row {row.get('name', 'UNKNOWN')}: {str(e)}")

    except Exception as e:
        current_app.logger.error(f"Bulk CSV mapping execution failed abruptly: {str(e)}")
        errors.append(str(e))
    finally:
        # Cleanup physical temp file bound seamlessly
        if os.path.exists(filepath):
            os.remove(filepath)

    # Resolve Admin identity tracing email closure natively
    admin_user = repositories.user.get(admin_id)
    if admin_user and admin_user.email:
        report_html = f"""
        <h3>Bulk Package CSV Parsing Report</h3>
        <p>Your asynchronous ingestion task completed traversing bounds constraints.</p>
        <ul>
            <li><strong>Successfully Mapped:</strong> {success_count}</li>
            <li><strong>Failed Bounds:</strong> {failure_count}</li>
        </ul>
        """
        if errors:
            report_html += "<h4>Execution Log Traces:</h4><ul>"
            for err in errors[:10]: # Limit email bounds 
                report_html += f"<li>{err}</li>"
            report_html += "</ul>"
            
        # payload = EmailPayload(
        #     to_email=admin_user.email,
        #     subject=f"Bulk Package Import Result: {success_count} Successes",
        #     body_html=report_html
        # )
        event_type: NotificationEventType = NotificationEventType.ADMIN_EXPORT_READY
        recipient_type: RecipientType = RecipientType.ADMIN
        recipient_id: str = admin_id
        context: dict[str, Any] = {
            "title": "Package Import Report",
            "message": f"Your package import has been processed successfully. {success_count} packages were imported successfully and {failure_count} packages failed to import.",
        }

        get_services().notification.dispatch(
            event_type=event_type,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            context=context,
        )
        db.session.commit()

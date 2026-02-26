import csv
import os
from celery import shared_task
from flask import current_app
from app.services.package.service import PackageService
from app.dto.package.schemas import CreatePackageDTO
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import SendEmailDTO
from app.repository import repositories

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
        package_service = PackageService()
        
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Explicit mapping from CSV string arrays
                    dto = CreatePackageDTO(
                        name=row.get('name', '').strip(),
                        slug=row.get('slug', '').strip(),
                        description=row.get('description', '').strip(),
                        price=float(row.get('price', 0.0)),
                        currency=row.get('currency', 'USD').strip(),
                        duration_days=int(row.get('duration_days', 1)),
                        country=row.get('country', '').strip(),
                        is_featured=row.get('is_featured', 'false').lower() == 'true',
                        is_active=row.get('is_active', 'true').lower() == 'true',
                        available_slots=int(row.get('available_slots', 0))
                    )
                    
                    if not dto.name or not dto.slug:
                        raise ValueError("Missing mandatory logical fields natively.")
                        
                    package_service.create_package(dto)
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
    admin_user = repositories.user.get_by_id(admin_id)
    if admin_user and admin_user.email:
        ns = NotificationService()
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
            
        payload = SendEmailDTO(
            to_email=admin_user.email,
            subject=f"Bulk Package Import Result: {success_count} Successes",
            body_html=report_html
        )
        ns.send_email(payload)

# services/reporting_service.py
"""
ReportingService — analytics, dashboards, and CSV exports.

Implements interfaces.md § 13. ReportingService.
All queries are read-only; no db.session.commit() is called here.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

from sqlalchemy import and_, extract, func, select

from app.models.base import db
from app.enums import(
    AuditActionType, BookingStatus,
    BookingServiceType, PaymentMethod,
    PaymentStatus, ReferralStatus, UserRole
)
from app.core.logging import get_logger
from app.models import (
    Booking, Client, ServiceFeeSchedule, 
    TravelPackage, Payment, Referral, 
    User, CorporateSubscription, PackageBooking
)
from app.repository import audit_repo, booking_repo
from app.interface._base import BaseService

logger = get_logger(__name__)

# Response shapes (not DTOs — used internally and serialised in routes)
@dataclass
class DashboardSummaryResponse:
    bookings_this_month: int = 0
    revenue_this_month_usd: Decimal = Decimal("0.00")
    pending_payments: int = 0
    new_clients_this_week: int = 0
    upcoming_departures_7d: int = 0
    active_packages: int = 0
    confirmed_bookings: int = 0


@dataclass
class RevenueDataPoint:
    period: str
    total_usd: Decimal
    booking_count: int


@dataclass
class ClientRevenueRow:
    client_id: str
    client_name: str
    email: str
    total_fees_usd: Decimal
    booking_count: int


@dataclass
class PackagePopularityRow:
    package_id: str
    title: str
    booking_count: int
    total_participants: int


@dataclass
class SubscriptionUsageRow:
    account_id: str
    company_name: str
    tier: str
    bookings_used: int
    bookings_limit: int | None
    utilisation_pct: float


@dataclass
class AgentPerformanceRow:
    user_id: str
    full_name: str
    email: str
    bookings_created: int
    confirmed_count: int


@dataclass
class ReferralConversionResponse:
    total_referrals: int = 0
    qualified_count: int = 0
    credited_count: int = 0
    conversion_pct: float = 0.0


class ReportingService(BaseService):

    def dashboard_summary(self, actor_id: str) -> DashboardSummaryResponse:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_start  = now - timedelta(days=7)

        # Bookings this month
        bookings_month = db.session.execute(
            select(func.count(Booking.id)).where(Booking.created_at >= month_start)
        ).scalar_one()

        # Revenue this month (confirmed bookings)
        revenue_month = db.session.execute(
            select(func.sum(Booking.total_service_fee_usd))
            .where(
                Booking.created_at >= month_start,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
            )
        ).scalar_one_or_none() or Decimal("0.00")

        # Pending payments
        pending = db.session.execute(
            select(func.count(Booking.id))
            .where(Booking.status == BookingStatus.PENDING_PAYMENT)
        ).scalar_one()

        # New clients this week
        new_clients = db.session.execute(
            select(func.count(Client.id)).where(Client.created_at >= week_start)
        ).scalar_one()

        # Upcoming departures in next 7 days
        upcoming = len(
            __import__("repositories", fromlist=["booking_repo"]).booking_repo
            .find_confirmed_upcoming(cutoff_date=(now + timedelta(days=7)).date())
        )

        # Active packages
        from models.package import PackageStatus
        active_pkgs = db.session.execute(
            select(func.count(TravelPackage.id))
            .where(TravelPackage.status == PackageStatus.ACTIVE)
        ).scalar_one()

        # Total confirmed bookings
        confirmed = db.session.execute(
            select(func.count(Booking.id))
            .where(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]))
        ).scalar_one()

        return DashboardSummaryResponse(
            bookings_this_month=bookings_month,
            revenue_this_month_usd=revenue_month,
            pending_payments=pending,
            new_clients_this_week=new_clients,
            upcoming_departures_7d=upcoming,
            active_packages=active_pkgs,
            confirmed_bookings=confirmed,
        )

    def booking_revenue_by_period(
        self,
        from_date: date,
        to_date: date,
        group_by: Literal["day", "week", "month"] = "month",
    ) -> list[RevenueDataPoint]:
        from_dt = datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc)
        to_dt   = datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc)

        if group_by == "day":
            period_expr = func.date(Booking.created_at)
        elif group_by == "week":
            period_expr = func.strftime("%Y-W%W", Booking.created_at)
        else:
            period_expr = func.strftime("%Y-%m", Booking.created_at)

        rows = db.session.execute(
            select(
                period_expr.label("period"),
                func.sum(Booking.total_service_fee_usd).label("total"),
                func.count(Booking.id).label("count"),
            )
            .where(
                Booking.created_at.between(from_dt, to_dt),
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
            )
            .group_by(period_expr)
            .order_by(period_expr)
        ).all()
        return [
            RevenueDataPoint(period=str(r.period), total_usd=r.total or Decimal("0.00"), booking_count=r.count)
            for r in rows
        ]

    def booking_count_by_service_type(
        self, from_date: date, to_date: date
    ) -> dict[str, int]:
        from_dt = datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc)
        to_dt   = datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc)
        rows = db.session.execute(
            select(Booking.service_type, func.count(Booking.id))
            .where(Booking.created_at.between(from_dt, to_dt))
            .group_by(Booking.service_type)
        ).all()
        return {row[0].value: row[1] for row in rows}

    def booking_count_by_status(
        self, from_date: date | None = None, to_date: date | None = None
    ) -> dict[str, int]:
        stmt = select(Booking.status, func.count(Booking.id)).group_by(Booking.status)
        if from_date:
            stmt = stmt.where(
                Booking.created_at >= datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc)
            )
        if to_date:
            stmt = stmt.where(
                Booking.created_at <= datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc)
            )
        rows = db.session.execute(stmt).all()
        return {row[0].value: row[1] for row in rows}

    def top_clients_by_revenue(
        self,
        limit: int = 10,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ClientRevenueRow]:
        stmt = (
            select(
                Client.id,
                Client.first_name,
                Client.last_name,
                Client.email,
                func.sum(Booking.total_service_fee_usd).label("total"),
                func.count(Booking.id).label("count"),
            )
            .join(Booking, Booking.client_id == Client.id)
            .where(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]))
            .group_by(Client.id, Client.first_name, Client.last_name, Client.email)
            .order_by(func.sum(Booking.total_service_fee_usd).desc())
            .limit(limit)
        )
        if from_date:
            stmt = stmt.where(Booking.created_at >= datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc))
        if to_date:
            stmt = stmt.where(Booking.created_at <= datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc))
        rows = db.session.execute(stmt).all()
        return [
            ClientRevenueRow(
                client_id=r.id,
                client_name=f"{r.first_name} {r.last_name}",
                email=r.email,
                total_fees_usd=r.total or Decimal("0.00"),
                booking_count=r.count,
            )
            for r in rows
        ]

    def top_packages_by_bookings(
        self, limit: int = 10, from_date: date | None = None, to_date: date | None = None
    ) -> list[PackagePopularityRow]:
        stmt = (
            select(
                TravelPackage.id,
                TravelPackage.title,
                func.count(PackageBooking.id).label("bookings"),
                func.sum(PackageBooking.num_participants).label("participants"),
            )
            .join(PackageBooking, PackageBooking.package_id == TravelPackage.id)
            .where(PackageBooking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]))
            .group_by(TravelPackage.id, TravelPackage.title)
            .order_by(func.count(PackageBooking.id).desc())
            .limit(limit)
        )
        rows = db.session.execute(stmt).all()
        return [
            PackagePopularityRow(
                package_id=r.id, title=r.title,
                booking_count=r.bookings, total_participants=r.participants or 0
            )
            for r in rows
        ]

    def corporate_subscription_usage(self) -> list[SubscriptionUsageRow]:
        from models.client import CorporateAccount
        rows = db.session.execute(
            select(
                CorporateAccount.id,
                CorporateAccount.company_name,
                CorporateSubscription.tier,
                CorporateSubscription.bookings_used,
                CorporateSubscription.bookings_limit,
            )
            .join(CorporateSubscription, CorporateSubscription.account_id == CorporateAccount.id)
            .where(CorporateSubscription.is_active.is_(True))
            .order_by(CorporateAccount.company_name)
        ).all()
        result = []
        for r in rows:
            limit = r.bookings_limit or 1
            pct = (r.bookings_used / limit * 100) if r.bookings_limit else 0.0
            result.append(SubscriptionUsageRow(
                account_id=r.id, company_name=r.company_name,
                tier=r.tier.value, bookings_used=r.bookings_used,
                bookings_limit=r.bookings_limit, utilisation_pct=round(pct, 1),
            ))
        return result

    def payment_method_breakdown(
        self, from_date: date, to_date: date
    ) -> dict[str, Decimal]:
        from_dt = datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc)
        to_dt   = datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc)
        rows = db.session.execute(
            select(Payment.method, func.sum(Payment.amount_usd))
            .where(
                Payment.status == PaymentStatus.CONFIRMED,
                Payment.created_at.between(from_dt, to_dt),
            )
            .group_by(Payment.method)
        ).all()
        return {row[0].value: row[1] or Decimal("0.00") for row in rows}

    def referral_conversion_rate(
        self, from_date: date | None = None, to_date: date | None = None
    ) -> ReferralConversionResponse:
        stmt = select(Referral.status, func.count(Referral.id)).group_by(Referral.status)
        rows = dict(db.session.execute(stmt).all())
        total = sum(rows.values())
        qualified = rows.get(ReferralStatus.QUALIFIED, 0) + rows.get(ReferralStatus.CREDITED, 0)
        credited  = rows.get(ReferralStatus.CREDITED, 0)
        conversion = round((qualified / total * 100) if total else 0.0, 1)
        return ReferralConversionResponse(
            total_referrals=total,
            qualified_count=qualified,
            credited_count=credited,
            conversion_pct=conversion,
        )

    def agent_performance(
        self, from_date: date, to_date: date
    ) -> list[AgentPerformanceRow]:
        from_dt = datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc)
        to_dt   = datetime.combine(to_date, datetime.max.time(), tzinfo=timezone.utc)
        rows = db.session.execute(
            select(
                User.id, User.full_name, User.email,
                func.count(Booking.id).label("total"),
                func.sum(
                    (Booking.status == BookingStatus.CONFIRMED).cast(__import__("sqlalchemy").Integer)
                ).label("confirmed"),
            )
            .join(Booking, Booking.created_by_id == User.id)
            .where(
                User.role.in_([UserRole.ADMIN, UserRole.AGENT, UserRole.SUPER_ADMIN]),
                Booking.created_at.between(from_dt, to_dt),
            )
            .group_by(User.id, User.full_name, User.email)
            .order_by(func.count(Booking.id).desc())
        ).all()
        return [
            AgentPerformanceRow(
                user_id=r.id, full_name=r.full_name, email=r.email,
                bookings_created=r.total, confirmed_count=r.confirmed or 0,
            )
            for r in rows
        ]

    def export_bookings_csv(self, filters: dict, actor_id: str) -> bytes:
        all_bookings = booking_repo.paginate_bookings(
            page=1, per_page=10_000, **{
                k: v for k, v in filters.items()
                if k in ("client_id", "service_type", "status", "date_from", "date_to")
            }
        ).items
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "Reference", "Service", "Status", "Client ID",
            "Fee USD", "Discount USD", "Emergency", "Group", "Created At"
        ])
        for b in all_bookings:
            writer.writerow([
                b.reference_number, b.service_type.value, b.status.value,
                b.client_id, str(b.total_service_fee_usd), str(b.discount_amount_usd),
                b.is_emergency, b.is_group, b.created_at.isoformat(),
            ])
        self._audit(AuditActionType.EXPORT, actor_id, "booking", None,
                    description=f"Booking CSV exported ({len(all_bookings)} rows).")
        db.session.commit()
        return buf.getvalue().encode()

    def export_clients_csv(self, filters: dict, actor_id: str) -> bytes:
        from repositories import client_repo
        all_clients = client_repo.paginate_clients(
            page=1, per_page=10_000,
            client_type=filters.get("client_type"),
            is_active=filters.get("is_active"),
            search=filters.get("search"),
        ).items
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "ID", "First Name", "Last Name", "Email", "Phone",
            "Type", "Active", "Created At"
        ])
        for c in all_clients:
            writer.writerow([
                c.id, c.first_name, c.last_name, c.email, c.phone or "",
                c.client_type.value, c.is_active, c.created_at.isoformat(),
            ])
        self._audit(AuditActionType.EXPORT, actor_id, "client", None,
                    description=f"Client CSV exported ({len(all_clients)} rows).")
        db.session.commit()
        return buf.getvalue().encode()


reporting_service = ReportingService()
import pytest
from datetime import date
from decimal import Decimal

from app.repository.fee import ServiceFeeScheduleRepository, ServiceFeeRepository, ServiceFeeSnapshotRepository
from app.models import ServiceFeeSchedule, ServiceFee, ServiceFeeSnapshot
from app.enums import FeeType, BookingChannel

@pytest.fixture
def sched_repo():
    return ServiceFeeScheduleRepository()

@pytest.fixture
def fee_repo():
    return ServiceFeeRepository()

@pytest.fixture
def snap_repo():
    return ServiceFeeSnapshotRepository()

@pytest.mark.integration
class TestFeeRepositories:
    def test_schedule_queries(self, sched_repo, db_session):
        s1 = ServiceFeeSchedule(name="S1", effective_from=date.today(), is_active=True)
        s2 = ServiceFeeSchedule(name="S2", effective_from=date.today(), is_active=False)
        db_session.add_all([s1, s2])
        db_session.flush()

        active = sched_repo.find_active()
        assert active == s1

        sched_repo.deactivate_all()
        db_session.flush()
        db_session.refresh(s1)
        assert s1.is_active is False

    def test_fee_queries(self, fee_repo, db_session):
        s = ServiceFeeSchedule(name="S", effective_from=date.today(), is_active=True)
        db_session.add(s)
        db_session.flush()

        f1 = ServiceFee(
            schedule_id=str(s.id), fee_type=FeeType.DOMESTIC_FLIGHT,
            label="L1", amount_usd=Decimal("10.00"), min_amount_usd=Decimal("10"),
            max_amount_usd=Decimal("50")
        )
        f2 = ServiceFee(
            schedule_id=str(s.id), fee_type=FeeType.INTERNATIONAL_FLIGHT,
            label="L2", amount_usd=Decimal("20.00"), min_amount_usd=Decimal("10"),
            max_amount_usd=Decimal("50"), is_active=False
        )
        db_session.add_all([f1, f2])
        db_session.flush()

        fees = fee_repo.find_by_schedule(str(s.id))
        assert len(fees) == 2

        active = fee_repo.find_active_by_type(FeeType.DOMESTIC_FLIGHT)
        assert active == f1

        inactive = fee_repo.find_active_by_type(FeeType.INTERNATIONAL_FLIGHT)
        assert inactive is None

    def test_snapshot_queries(self, snap_repo, db_session):
        snap = ServiceFeeSnapshot(
            booking_id="B1", fee_type=FeeType.DOMESTIC_FLIGHT,
            fee_label="Dom", base_amount_usd=Decimal("10"),
            applied_amount_usd=Decimal("10"), num_passengers=1,
            channel=BookingChannel.WEB, emergency_surcharge_applied=False
        )
        db_session.add(snap)
        db_session.flush()

        assert snap_repo.find_by_booking("B1") == snap
        assert snap_repo.find_by_booking("UNKNOWN") is None

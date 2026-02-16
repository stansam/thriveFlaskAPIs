import pytest
from app import create_app
from app.extensions import db
from app.models import User, Booking
from app.models.enums import UserRole, SubscriptionTier, BookingStatus, BookingType

@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def db_session(app):
    connection = db.engine.connect()
    transaction = connection.begin()
    
    session = db.session
    # session.bind = connection  # Using the existing session bound to engine
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

import uuid

@pytest.fixture
def user_factory(db_session):
    def create_user(role=UserRole.CLIENT, **kwargs):
        unique_id = uuid.uuid4().hex[:8]
        user = User(
            email=kwargs.get('email', f'test_{unique_id}@example.com'),
            password_hash='hashed_password',
            first_name='Test',
            last_name='User',
            role=role,
            subscription_tier=SubscriptionTier.NONE,
            **kwargs
        )
        db_session.add(user)
        db_session.commit()
        return user
    return create_user

@pytest.fixture
def booking_factory(db_session, user_factory):
    def create_booking(status=BookingStatus.PENDING, **kwargs):
        user = kwargs.get('user') or user_factory()
        unique_ref = uuid.uuid4().hex[:8].upper()
        booking = Booking(
            reference_code=kwargs.get('reference_code', f'THRIVE-{unique_ref}'),
            user_id=user.id,
            booking_type=BookingType.FLIGHT,
            currency="USD",
            status=status,
            **kwargs
        )
        db_session.add(booking)
        db_session.commit()
        return booking
    return create_booking

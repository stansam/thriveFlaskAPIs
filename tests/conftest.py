import pytest
from app import create_app
from app.extensions import db
from app.models import User, Booking
from app.models.enums import UserRole, SubscriptionTier, BookingStatus, BookingType
import uuid

@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='session')
def client(app):
    return app.test_client()

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

@pytest.fixture
def user_factory(db_session):
    def create_user(role=UserRole.CLIENT, **kwargs):
        unique_id = uuid.uuid4().hex[:8]
        password = kwargs.pop('password', 'hashed_password')
        email = kwargs.pop('email', f'test_{unique_id}@example.com')
        
        user = User(
            email=email,
            password_hash='hashed_password', # Temporary placeholder, overwritten below if needed
            first_name='Test',
            last_name='User',
            role=role,
            subscription_tier=SubscriptionTier.NONE,
            **kwargs
        )
        # If password was passed (or default), hash it properly
        # But wait, 'hashed_password' string is not a valid hash for check_password.
        # So we should always set_password if we want login to work.
        if password == 'hashed_password':
             user.password_hash = 'hashed_password' # Keep dummy if not specified
        else:
             user.set_password(password)

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

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import uuid
from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import UserRole, SubscriptionTier, Gender

class User(UserMixin, BaseModel):
    __tablename__ = 'users'
    
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum(UserRole), default=UserRole.CLIENT, nullable=False)
    gender = db.Column(db.Enum(Gender), nullable=True)
    
    email_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    email_verification_token = db.Column(db.String(100))
    email_verification_token_expires_at = db.Column(db.DateTime)
    locale = db.Column(db.String(10))

    avatar_url = db.Column(db.String(255))
    referral_code = db.Column(db.String(20), unique=True)
    referral_credits = db.Column(db.Float, default=0.0)
    referrer_id = db.Column(db.String(36), db.ForeignKey('users.id')) 
    
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'))
    
    preferences = db.relationship('UserPreference', backref='user', uselist=False, cascade="all, delete-orphan")

    last_login = db.Column(db.DateTime)
    
    subscription_tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.NONE)
    subscription_end = db.Column(db.DateTime)
    monthly_bookings_used = db.Column(db.Integer, default=0)

    bookings = db.relationship('Booking', backref='customer', lazy='dynamic', foreign_keys='Booking.user_id')
    payments = db.relationship('Payment', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    referrals = db.relationship('User', backref=db.backref('referrer', remote_side="User.id"))

    favorite_packages = db.relationship(
        'Package', 
        secondary='user_favorites', 
        backref=db.backref('favorited_by', lazy='dynamic'), 
        lazy='dynamic'
    )
    user_favorites = db.Table('user_favorites',
        db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
        db.Column('package_id', db.String(36), db.ForeignKey('packages.id'), primary_key=True),
        db.Column('created_at', db.DateTime, default=datetime.now(timezone.utc))
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def has_active_subscription(self):
        if not self.subscription_end:
            return False
        end = self.subscription_end
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < end
    
    def can_book(self):
        if self.subscription_tier == SubscriptionTier.GOLD:
            return True
        elif self.subscription_tier == SubscriptionTier.SILVER:
            return self.monthly_bookings_used < 15
        elif self.subscription_tier == SubscriptionTier.BRONZE:
            return self.monthly_bookings_used < 6
        return True  
    
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role.value,
            'gender': self.gender.value if self.gender else None,
            'subscription_tier': self.subscription_tier.value,
            'referral_code': self.referral_code,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'referral_credits': float(self.referral_credits)
        }

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

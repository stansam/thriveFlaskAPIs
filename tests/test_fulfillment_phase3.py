import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from app.models import Booking, Payment
from app.models.enums import BookingStatus, PaymentStatus, PaymentMethod, UserRole

def test_verify_payment_success(client, booking_factory):
    booking = booking_factory()
    # Setup: Booking is AWAITING_VERIFICATION, Payment is PENDING
    booking.status = BookingStatus.AWAITING_VERIFICATION
    from app.extensions import db
    db.session.add(Payment(
        booking_id=booking.id,
        user_id=booking.user_id,
        amount=100.0,
        payment_method=PaymentMethod.MANUAL_TRANSFER,
        status=PaymentStatus.PENDING,
        receipt_url="receipt.jpg"
    ))
    db.session.commit()

    # Create admin user mock
    admin_user = MagicMock()
    admin_user.role = UserRole.ADMIN
    admin_user.id = "admin_id"
    admin_user.is_authenticated = True

    with patch('flask_login.utils._get_user') as mock_user:
        mock_user.return_value = admin_user

        response = client.post(
            f'/api/admin/booking/{booking.id}/verify',
            json={"status": "approved"}
        )
        
        assert response.status_code == 200
        json_resp = response.get_json()
        assert json_resp['message'] == "Payment verified"
        
        # Check DB
        db.session.refresh(booking)
        payment = db.session.query(Payment).filter_by(booking_id=booking.id).first()
        
        assert booking.status == BookingStatus.CONFIRMED
        assert payment.status == PaymentStatus.PAID

def test_verify_payment_failure(client, booking_factory):
    booking = booking_factory()
    booking.status = BookingStatus.AWAITING_VERIFICATION
    from app.extensions import db
    db.session.add(Payment(
        booking_id=booking.id,
        user_id=booking.user_id,
        amount=100.0,
        payment_method=PaymentMethod.MANUAL_TRANSFER,
        status=PaymentStatus.PENDING,
        receipt_url="receipt.jpg"
    ))
    db.session.commit()

    admin_user = MagicMock()
    admin_user.role = UserRole.ADMIN
    admin_user.id = "admin_id"
    admin_user.is_authenticated = True

    with patch('flask_login.utils._get_user') as mock_user:
        mock_user.return_value = admin_user

        response = client.post(
            f'/api/admin/booking/{booking.id}/verify',
            json={"status": "rejected", "rejection_reason": "Blurry image"}
        )
        
        assert response.status_code == 200
        json_resp = response.get_json()
        assert json_resp['message'] == "Payment rejected"
        
        db.session.refresh(booking)
        payment = db.session.query(Payment).filter_by(booking_id=booking.id).first()
        
        assert booking.status == BookingStatus.FAILED
        assert payment.status == PaymentStatus.FAILED

def test_upload_ticket_success(client, booking_factory):
    booking = booking_factory()
    booking.status = BookingStatus.CONFIRMED
    from app.extensions import db
    db.session.commit()
    
    # Mock FlightBooking existence
    from app.models import FlightBooking
    from app.models.enums import TravelClass
    fb = FlightBooking(
        booking_id=booking.id,
        pnr_reference="TESTPNR",
        cabin_class=TravelClass.ECONOMY
    )
    db.session.add(fb)
    db.session.commit()

    admin_user = MagicMock()
    admin_user.role = UserRole.ADMIN
    admin_user.id = "admin_id"
    admin_user.is_authenticated = True

    with patch('app.utils.upload.UploadService.save_file') as mock_save, \
         patch('flask_login.utils._get_user') as mock_user:
        
        mock_user.return_value = admin_user
        mock_save.return_value = "tickets/ticket.pdf"
        
        data = {
            'file': (BytesIO(b"PDF data"), 'ticket.pdf')
        }
        
        response = client.post(
            f'/api/admin/booking/{booking.id}/ticket',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        json_resp = response.get_json()
        assert json_resp['message'] == "Ticket uploaded successfully"
        assert json_resp['ticket_url'] == "tickets/ticket.pdf"
        
        db.session.refresh(booking)
        assert booking.status == BookingStatus.TICKETED

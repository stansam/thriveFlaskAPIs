import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from app.models import Booking, Payment
from app.models.enums import BookingStatus, PaymentStatus, PaymentMethod

def test_upload_payment_proof_success(client, booking_factory):
    # Create a booking
    booking = booking_factory()
    # Ensure it is in PENDING state
    booking.status = BookingStatus.PENDING
    from app.extensions import db
    db.session.commit()

    # Mock UploadService to avoid actual file saving and Login
    with patch('app.utils.upload.UploadService.save_file') as mock_save, \
         patch('flask_login.utils._get_user') as mock_user:
        
        # We need a user object. The booking factory creates one but doesn't attach 'user' obj to booking instance by default if lazy
        # But booking.user_id exists. Let's create a mock user with that ID.
        user_mock = MagicMock()
        user_mock.id = booking.user_id
        user_mock.is_authenticated = True
        mock_user.return_value = user_mock
        mock_save.return_value = "receipts/2026/02/test_receipt.jpg"
        
        data = {
            'file': (BytesIO(b"fake image data"), 'receipt.jpg')
        }
        
        response = client.post(
            f'/api/booking/{booking.id}/payment-proof', 
            data=data, 
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 201
        json_resp = response.get_json()
        assert json_resp['message'] == "Payment proof uploaded successfully"
        assert json_resp['receipt_url'] == "receipts/2026/02/test_receipt.jpg"
        
        # Verify DB Side Effects
        db.session.refresh(booking)
        assert booking.status == BookingStatus.AWAITING_VERIFICATION
        
        payment = db.session.query(Payment).filter_by(booking_id=booking.id).first()
        assert payment is not None
        assert payment.receipt_url == "receipts/2026/02/test_receipt.jpg"
        assert payment.status == PaymentStatus.PENDING
        assert payment.payment_method == PaymentMethod.MANUAL_TRANSFER

def test_upload_payment_proof_invalid_file(client, booking_factory):
    booking = booking_factory()
    
    with patch('app.utils.upload.UploadService.save_file') as mock_save, \
         patch('flask_login.utils._get_user') as mock_user:
        
        user_mock = MagicMock()
        user_mock.id = booking.user_id
        user_mock.is_authenticated = True
        mock_user.return_value = user_mock
        mock_save.side_effect = ValueError("File type not allowed")
        
        data = {
            'file': (BytesIO(b"malicious script"), 'script.sh')
        }
        
        response = client.post(
            f'/api/booking/{booking.id}/payment-proof', 
            data=data, 
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        assert "File type not allowed" in response.get_json()['message']

def test_upload_payment_proof_booking_not_found(client, user_factory):
    # Need a user to be logged in, even if booking doesn't exist?
    # Actually, the route checks booking first, then auth.
    # But wait, logic says:
    # 1. Get Booking (might fail 404)
    # 2. Check Auth (needs current_user)
    # If 404 happens first, we might not need auth mock?
    # BUT, MethodView decorators run BEFORE function body.
    # @login_required runs first.
    # So we MUST mock login.
    
    user = user_factory()
    with patch('flask_login.utils._get_user') as mock_user:
        mock_user.return_value = user
        
        data = {
            'file': (BytesIO(b"fake image data"), 'receipt.jpg')
        }
        response = client.post(
            '/api/booking/non_existent_id/payment-proof', 
            data=data, 
            content_type='multipart/form-data'
        )
        assert response.status_code == 404

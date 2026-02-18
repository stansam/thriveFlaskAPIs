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

    # Mock UploadService to avoid actual file saving
    with patch('app.utils.upload.UploadService.save_file') as mock_save:
        mock_save.return_value = "receipts/2026/02/test_receipt.jpg"
        
        data = {
            'file': (BytesIO(b"fake image data"), 'receipt.jpg')
        }
        
        # Add Header for Auth bypass (Phase 3 Dev)
        headers = {'X-Test-User-ID': booking.user_id}
        
        response = client.post(
            f'/api/booking/{booking.id}/payment-proof', 
            data=data, 
            content_type='multipart/form-data',
            headers=headers
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
    
    with patch('app.utils.upload.UploadService.save_file') as mock_save:
        mock_save.side_effect = ValueError("File type not allowed")
        
        data = {
            'file': (BytesIO(b"malicious script"), 'script.sh')
        }
        headers = {'X-Test-User-ID': booking.user_id}
        
        response = client.post(
            f'/api/booking/{booking.id}/payment-proof', 
            data=data, 
            content_type='multipart/form-data',
            headers=headers
        )
        
        assert response.status_code == 400
        assert "File type not allowed" in response.get_json()['message']

def test_upload_payment_proof_booking_not_found(client):
    data = {
        'file': (BytesIO(b"fake image data"), 'receipt.jpg')
    }
    response = client.post(
        '/api/booking/non_existent_id/payment-proof', 
        data=data, 
        content_type='multipart/form-data'
    )
    assert response.status_code == 404

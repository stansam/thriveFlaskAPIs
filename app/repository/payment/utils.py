import logging
from app.models.enums import PaymentStatus

logger = logging.getLogger(__name__)

def parse_gateway_status(raw_status: str) -> PaymentStatus:
    """
    Normalizes erratic string representations returned by disparate Gateways 
    like Stripe ('succeeded', 'failed') or Pesapal ('COMPLETED', 'INVALID') 
    into absolute internal Enums.
    """
    cln = raw_status.strip().upper()
    
    if cln in ['SUCCEEDED', 'COMPLETED', 'PAID', 'SUCCESS']:
        return PaymentStatus.COMPLETED
    elif cln in ['FAILED', 'INVALID', 'DECLINED', 'REJECTED']:
        return PaymentStatus.FAILED
    elif cln in ['REFUNDED']:
        return PaymentStatus.REFUNDED
    else:
        # Failsafe default retaining PENDING until manual intervention
        logger.warning(f"Unrecognized Payment Gateway Status payload intercepted: {raw_status}")
        return PaymentStatus.PENDING

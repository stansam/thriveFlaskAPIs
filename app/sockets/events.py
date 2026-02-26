import logging
from flask import request
from flask_socketio import emit
from app.extensions import socketio

logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    """
    Establishes the physical socket upgrade natively securing the telemetry pipe.
    """
    logger.info(f"Client socket securely bridged constraints: {request.sid}")
    emit('server_acked', {'status': 'Connected natively'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected safely tearing down telemetry: {request.sid}")

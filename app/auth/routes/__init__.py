from app.auth import auth_bp
from app.auth.routes.login import Login
from app.auth.routes.register import Register
from app.auth.routes.google import Google
from app.auth.routes.verify_email import VerifyEmail, ResendVerification
from app.auth.routes.reset_password import ForgotPassword, ResetPassword

auth_bp.add_url_rule('/login', view_func=Login.as_view('login'))
auth_bp.add_url_rule('/register', view_func=Register.as_view('register'))
auth_bp.add_url_rule('/google', view_func=Google.as_view('google'))
auth_bp.add_url_rule('/verify-email', view_func=VerifyEmail.as_view('verify_email'))
auth_bp.add_url_rule('/resend-verification', view_func=ResendVerification.as_view('resend_verification'))
auth_bp.add_url_rule('/forgot-password', view_func=ForgotPassword.as_view('forgot_password'))
auth_bp.add_url_rule('/reset-password', view_func=ResetPassword.as_view('reset_password'))

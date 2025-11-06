import os

# XAMPP/MySQL defaults; change if needed
DB_HOST = os.getenv("DB_HOST","localhost")
DB_USER = os.getenv("DB_USER","root")
DB_PASSWORD = os.getenv("DB_PASSWORD","")
DB_NAME = os.getenv("DB_NAME","ic_smart_library")

# Secret for signing QR payloads and Flask sessions
SECRET_KEY = os.getenv("SECRET_KEY","super-secret-smartcecilian")
QR_HMAC_SECRET = os.getenv("QR_HMAC_SECRET","qr-secret-smartcecilian").encode()

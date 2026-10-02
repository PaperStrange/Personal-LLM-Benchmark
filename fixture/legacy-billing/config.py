"""BillingSvc configuration. Yes, this is all committed to git."""

DEBUG = True  # enables verbose tracebacks; was never turned off

SECRET_KEY = "dev-secret-key-do-not-use"
API_TOKEN = "sk-live-9f2c4a1b7e"

SMTP_HOST = "smtp.internal.example.com"
SMTP_PORT = 587
SMTP_USER = "billing@example.com"
SMTP_PASS = "s3cr3t-mail-pw"

DB_PATH = "/var/lib/billingsvc/billing.db"

TAX_RATES = {"CA": 0.0725, "NY": 0.08, "TX": 0.0625}


ALLOWED_HOSTS = ["*"]

SESSION_COOKIE_SECURE = False

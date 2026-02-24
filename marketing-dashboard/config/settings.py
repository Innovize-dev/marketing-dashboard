import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Google Ads ──────────────────────────────────────────────────────────
    GOOGLE_ADS_DEVELOPER_TOKEN: str = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
    GOOGLE_ADS_CLIENT_ID: str = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
    GOOGLE_ADS_CLIENT_SECRET: str = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")
    GOOGLE_ADS_REFRESH_TOKEN: str = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "")
    GOOGLE_ADS_CUSTOMER_ID: str = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
    GOOGLE_ADS_LOGIN_CUSTOMER_ID: str = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")

    # ── Google Analytics 4 ──────────────────────────────────────────────────
    GA4_PROPERTY_ID: str = os.getenv("GA4_PROPERTY_ID", "")
    # Either a path to a service-account JSON file OR the raw JSON string
    GA4_SERVICE_ACCOUNT_JSON: str = os.getenv("GA4_SERVICE_ACCOUNT_JSON", "")

    # ── Meta (Facebook / Instagram) ─────────────────────────────────────────
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    META_ACCESS_TOKEN: str = os.getenv("META_ACCESS_TOKEN", "")
    META_AD_ACCOUNT_ID: str = os.getenv("META_AD_ACCOUNT_ID", "")

    # ── TikTok Ads ──────────────────────────────────────────────────────────
    TIKTOK_ACCESS_TOKEN: str = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    TIKTOK_ADVERTISER_ID: str = os.getenv("TIKTOK_ADVERTISER_ID", "")

    # ── Reddit Ads ──────────────────────────────────────────────────────────
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_ACCESS_TOKEN: str = os.getenv("REDDIT_ACCESS_TOKEN", "")
    REDDIT_ACCOUNT_ID: str = os.getenv("REDDIT_ACCOUNT_ID", "")

    # ── App ─────────────────────────────────────────────────────────────────
    DB_PATH: str = os.getenv("DB_PATH", "data/dashboard.db")
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    # Fernet key for encrypting credentials in SQLite.
    # Generate once with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")


settings = Settings()

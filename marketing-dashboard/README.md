# Marketing Agency Reporting Dashboard

Internal Streamlit dashboard for viewing paid ad performance across Google Ads, GA4, Meta, TikTok, and Reddit.

---

## Setup

### 1. Install Python dependencies

```bash
cd marketing-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

- **ENCRYPTION_KEY** — generate with:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- Platform credentials (see below for how to obtain each)

### 3. Run the dashboard

```bash
streamlit run app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## Getting API Credentials

### Google Ads
1. Apply for a [Google Ads Developer Token](https://developers.google.com/google-ads/api/docs/first-call/dev-token)
2. Create an OAuth 2.0 client in [Google Cloud Console](https://console.cloud.google.com/)
3. Use the [OAuth Playground](https://developers.google.com/oauthplayground/) or `google-auth-oauthlib` to generate a refresh token
4. Your Customer ID is the 10-digit number in the top-right of Google Ads Manager (remove dashes)

### GA4
1. Go to [Google Cloud Console](https://console.cloud.google.com/) → IAM → Service Accounts
2. Create a service account, download the JSON key
3. In GA4 → Admin → Property Access Management, add the service account email with Viewer role
4. Your Property ID is under GA4 → Admin → Property Settings

### Meta
1. Go to [Meta for Developers](https://developers.facebook.com/) → Create App
2. Add the **Marketing API** product
3. Generate a long-lived User Access Token or System User Token
4. Your Ad Account ID is in Meta Business Suite → Ad Accounts (format: `act_XXXXXXXXXX`)

### TikTok
1. Apply for the [TikTok Marketing API](https://ads.tiktok.com/marketing_api/docs)
2. Complete the OAuth 2.0 flow to obtain an access token
3. Your Advertiser ID is visible in TikTok Ads Manager URL

### Reddit
1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps) → Create App (type: script or web)
2. Complete OAuth 2.0 to obtain an access token with `ads:read` scope
3. Your Account ID is your Reddit user account ID (t2_XXXXXXXX format — find via Reddit API)

---

## Architecture

```
integrations/    # One adapter per platform (all implement PlatformAdapter ABC)
pipeline/        # Fetch → Transform → Merge → Metrics
storage/         # SQLite (credentials + cache + audit log)
components/      # Reusable Streamlit UI widgets
pages/           # One Streamlit page per platform + Overview + Settings
```

**Data flow:** `fetcher.py` runs all platform API calls in parallel threads, caches results in SQLite for 1 hour, then the transformer/merger/metrics pipeline builds the final DataFrame shown in the table.

---

## Notes

- **GA4 join**: GA4 and Google Ads use different campaign ID systems. The join is done by `campaign_name` — ensure campaign names match exactly between Google Ads and GA4.
- **Interactions**: Platform-specific — Google Ads = interactions metric; Meta = post engagements; TikTok = video play actions; Reddit = clicks.
- **Token expiry**: Meta long-lived tokens expire after 60 days. TikTok tokens vary by app configuration. Renew tokens in the Settings page.
- **Cache TTL**: Default 1 hour, set `CACHE_TTL_SECONDS` in `.env`. Clear cache from Settings page if you need fresh data immediately.

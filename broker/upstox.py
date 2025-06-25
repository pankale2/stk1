from config.config import UPSTOX_API_KEY, UPSTOX_API_SECRET

def upstox_login_url(api_key=None):
    key = api_key if api_key else UPSTOX_API_KEY
    # Upstox login URL format as per docs
    return f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={key}&redirect_uri=YOUR_REDIRECT_URI"
# Replace YOUR_REDIRECT_URI with your actual redirect URI registered with Upstox
# Replace YOUR_REDIRECT_URI with your actual redirect URI registered with Upstox

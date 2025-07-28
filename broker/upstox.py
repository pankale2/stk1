from config.config import UPSTOX_API_KEY, UPSTOX_API_SECRET

def upstox_login_url(api_key=None):
    key = api_key if api_key else UPSTOX_API_KEY
    redirect_uri = "http://localhost:5050/callback"
    # Upstox login URL format as per docs
    return f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={key}&redirect_uri={redirect_uri}"

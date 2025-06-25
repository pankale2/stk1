from flask import Flask, render_template, redirect, url_for, request, session
from broker.upstox import upstox_login_url
import requests
from upstox_client import Configuration, ApiClient

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session

@app.route('/')
def home():
    return '<a href="/login">Login with Upstox</a>'

@app.route('/login', methods=['GET'])
def login():
    # Render a login form for Upstox API key and secret
    return render_template('login.html')

@app.route('/login/submit', methods=['POST'])
def login_submit():
    api_key = request.form.get('api_key')
    api_secret = request.form.get('api_secret')
    # Store in session for later use
    session['api_key'] = api_key
    session['api_secret'] = api_secret
    # Redirect to Upstox login URL (optionally, pass api_key if needed)
    return redirect(upstox_login_url(api_key))

@app.route('/callback')
def upstox_callback():
    code = request.args.get('code')
    api_key = session.get('api_key')
    api_secret = session.get('api_secret')
    redirect_uri = "YOUR_REDIRECT_URI"  # Must match what you used in upstox_login_url

    # Exchange code for access token
    response = requests.post(
        "https://api.upstox.com/v2/login/authorization/token",
        data={
            "code": code,
            "client_id": api_key,
            "client_secret": api_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
    )
    token_data = response.json()
    access_token = token_data.get("access_token")
    # Store access_token in session or database as needed

    # Example: instantiate Upstox object
    # u = Upstox(api_key, access_token)
    # ... use u for further API calls ...

    return f"Access token: {access_token}"

if __name__ == '__main__':
    app.run(debug=True)
# stk1: Upstox Portfolio Viewer

A Flask web application that connects to your Upstox account and displays your portfolio holdings in real-time with a beautiful, responsive interface.

## 🚀 Features
- **Secure OAuth2 Authentication**: Login with your Upstox API credentials
- **Real-time Portfolio**: View your current holdings with live market data  
- **P&L Calculations**: See profit/loss for each holding with percentage changes
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Session Management**: Secure session-based authentication with logout functionality

## 📁 Project Structure
```
app.py                # Main Flask application
broker/               # Upstox OAuth helper functions
  ├── upstox.py       # Login URL generation
  └── __init__.py
config/               # Configuration files
  ├── config.py       # API keys configuration
  └── __init__.py
templates/            # HTML templates
  ├── index.html      # Home page
  ├── login.html      # Login form
  └── holdings.html   # Holdings display
requirements.txt      # Python dependencies
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.7+
- Upstox Developer Account with API credentials

### 1. Get Upstox API Credentials
1. Visit [Upstox Developer Console](https://upstox.com/developer/apps)
2. Create a new app and get your API Key and Secret
3. Set redirect URI as: `http://localhost:5050/callback`

### 2. Install Dependencies
```powershell
# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Keys
Edit `config/config.py` and add your credentials:
```python
UPSTOX_API_KEY = "your_actual_api_key_here"
UPSTOX_API_SECRET = "your_actual_api_secret_here"
```

### 4. Run the Application
```powershell
python app.py
```

## 📱 Usage
1. **Start the app**: Open http://localhost:5050 in your browser
2. **Login**: Click "Login with Upstox" and enter your API credentials
3. **Authorize**: You'll be redirected to Upstox for authorization
4. **View Holdings**: After successful login, view your portfolio holdings
5. **Logout**: Use the logout button to end your session securely

## 🔐 Security Features
- Session-based authentication
- Secure token storage
- Automatic session cleanup on logout
- Input validation and error handling

## 📊 Holdings Display
The holdings page shows:
- Stock symbol and company name
- Quantity held
- Average purchase price
- Current market price  
- Total market value
- Profit/Loss amount and percentage
- Color-coded P&L (green for profit, red for loss)

## 🔧 Configuration
- **Session Secret**: Change `app.secret_key` in `app.py` for production
- **Redirect URI**: Must match exactly in both code and Upstox app settings
- **API Endpoints**: Uses Upstox API v2 endpoints

## References
- [Upstox Python SDK Documentation](https://github.com/upstox/upstox-python)
- [Upstox API Documentation](https://upstox.com/developer/api-documentation/)

# stk1: Flask App Using Upstox Python SDK

This project is a sample Flask web application that demonstrates how to integrate with the Upstox API using the official Upstox Python SDK.

## Features
- User login with Upstox API key/secret
- OAuth2 flow to obtain access token
- Example code for Upstox API usage

## Project Structure
```
app.py                # Main Flask app
broker/               # Upstox login URL helper
config/               # App configuration
requirements.txt      # Python dependencies
templates/            # HTML templates (login form)
```

## Requirements
- Python 3.7+
- See `requirements.txt` for dependencies

## Setup
1. Create a virtual environment (optional but recommended):
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Usage
1. Set your Upstox API key/secret in the login form.
2. Run the Flask app:
   ```powershell
   python app.py
   ```
3. Open http://localhost:5000 in your browser and follow the login flow.

## References
- [Upstox Python SDK Documentation](https://github.com/upstox/upstox-python)
- [Upstox API Documentation](https://upstox.com/developer/api-documentation/)

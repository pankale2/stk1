from flask import Flask, render_template, redirect, url_for
from broker.kite import kite_login_url

app = Flask(__name__)

@app.route('/')
def home():
    return '<a href="/login">Login with Kite</a>'

@app.route('/login')
def login():
    return redirect(kite_login_url())

if __name__ == '__main__':
    app.run(debug=True)
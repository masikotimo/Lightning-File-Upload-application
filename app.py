from flask import Flask, render_template, request, session, redirect, url_for
import os
import sqlite3
from lnd_grpc import Client, LightningRpc

app = Flask(__name__)
app.secret_key = 'secret_key'  # Change this to your own secret key

# Set up LND client
lnd = Client()

# Set up file storage directory
UPLOAD_FOLDER = 'uploads'
initial_free_sats = 10
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set up Lightning Network invoice amount
INVOICE_AMOUNT = 5000  # 5000 satoshis

# Set up SQLite database connection
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

# Create users table if it does not exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, username TEXT, password TEXT, balance INTEGER)''')
conn.commit()

# Define home page
@app.route('/', methods=['GET'])
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

# Define registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        # Check if username already exists in database
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        if user:
            return 'Username already exists'
        # Create new user
        c.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (username, password, initial_free_sats))
        conn.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Define login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        # Check if username and password are correct
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        if user:
            # Set session variables and redirect to dashboard
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return 'Incorrect username or password'
    return render_template('login.html')

# Define dashboard page
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Generate Lightning Network invoice
        invoice = lnd.add_invoice(INVOICE_AMOUNT)
        # Update user's balance in database
        c.execute("UPDATE users SET balance=balance+? WHERE username=?", (INVOICE_AMOUNT, session['username']))
        conn.commit()
        # Return Lightning Network invoice to user for payment
        return "invoice.payment_request"
    # Get user's balance from database
    c.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
    balance = c.fetchone()[0]
    return render_template('dashboard.html', balance=balance)

# Define logout function
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, session, redirect, url_for 
import os
import sqlite3
from lnd_grpc import Client
from werkzeug.utils import secure_filename
from constants import lnd_dir, tls_cert_path, grpc_port, grpc_host,macaroon_path,network


app = Flask(__name__)
app.secret_key = os.urandom(24)  

# Set up LND client
lnd = Client(lnd_dir = lnd_dir,macaroon_path= macaroon_path, tls_cert_path= tls_cert_path,network = network,grpc_host= grpc_host,grpc_port=grpc_port)

# Set up file storage directory
UPLOAD_FOLDER = 'uploads'
initial_free_sats = 10
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx','png'}

# Function to check if a given filename has an allowed extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Set up SQLite database connection
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

# Create users table if it does not exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, username TEXT, password TEXT, balance INTEGER, lnd_dir TEXT,macaroon_path TEXT,tls_cert_path TEXT, grpc_port TEXT)''')
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

        lnd_dir = request.form['lnd_dir']
        tls_cert_path= request.form['tls_cert_path']
        grpc_port = request.form['port']
        macaroon_path = request.form['macaroon_path']
        # Check if username already exists in database
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        if user:
            return 'Username already exists'
        # Create new user
        c.execute("INSERT INTO users (username, password, balance, lnd_dir,tls_cert_path,grpc_port,macaroon_path) VALUES (?, ?, ?,?, ?, ?,?)", (username, password, initial_free_sats,lnd_dir,tls_cert_path,grpc_port,macaroon_path))
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
        amount_deposited = request.form['amount']
        # Generate Lightning Network invoice
        invoice = lnd.add_invoice(value= int(amount_deposited) ,memo="pay_space" )

        c.execute("SELECT lnd_dir ,macaroon_path ,tls_cert_path , grpc_port FROM users WHERE username=?", (session['username'],))
        user= c.fetchone()
        if user:
            client_lnd_dir = user[0]  
            client_macaroon_path =user[1] 
            client_tls_cert_path = user[2]
            client_grpc_port = user[3]
            lnd2= Client(lnd_dir = client_lnd_dir,macaroon_path= client_macaroon_path, tls_cert_path= client_tls_cert_path,network = network,grpc_host= grpc_host,grpc_port=client_grpc_port)    
            
            print("my invoice",invoice.payment_request)
            response = lnd2.pay_invoice(payment_request = invoice.payment_request)

            if response.payment_hash:
                # Update user's balance in database
                c.execute("UPDATE users SET balance=balance+? WHERE username=?", (int(amount_deposited) , session['username']))
                conn.commit()
                return "You have successfully paid for extra file upload space"

            else:
                return "Opps something went wrong , Please try again later"
    # Get user's balance from database
    c.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
    balance = c.fetchone()[0]
    return render_template('dashboard.html', balance=balance)

# Define logout function
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return 'No file part'
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return 'No selected file'
        
        # Check if the file has an allowed extension
        if not allowed_file(file.filename):
            return 'Invalid file extension'
        
        
        if file and allowed_file(file.filename):
            c.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
            balance = c.fetchone()[0]

            if not balance > 0:
                return 'File size exceeded your available sats'

            # if int(request.content_length) > 1 * 1024 * 1024: # This will be incase i would like to use file size as an option to reduce sats
            #     return 'File size exceeded your available sats'
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            c.execute("UPDATE users SET balance=? WHERE username=?", ((balance-1) , session['username']))
            conn.commit()
            return 'File uploaded successfully'
        else:
            return 'File type not allowed'


    # Render the template for uploading documents
    return render_template('upload.html')





if __name__ == '__main__':
    app.run(debug=True)

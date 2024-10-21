from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client.user_identification
users = db.users

# Upload folder for profile pictures
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions for profile photo
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        dob = request.form['dob']
        password = request.form['password']
        photo = request.files['photo']

        # Check if email or mobile already exists
        if users.find_one({'email': email}):
            flash('This email is already registered.')
            return redirect(url_for('signup'))
        
        if users.find_one({'mobile': mobile}):
            flash('This mobile number is already registered.')
            return redirect(url_for('signup'))

        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None  # Set filename to None if no valid photo is uploaded

        hashed_password = generate_password_hash(password)
        
        # Insert user data into MongoDB
        users.insert_one({
            'name': name,
            'email': email,
            'mobile': mobile,
            'dob': dob,
            'password': hashed_password,
            'photo': filename
        })

        flash('Signup successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            session['email'] = user['email']
            return redirect(url_for('home'))

        flash('Invalid email or password!')
    return render_template('login.html')

@app.route('/home')
def home():
    if 'email' not in session:
        return redirect(url_for('login'))

    user = users.find_one({'email': session['email']})

    # Calculate age from date of birth
    if user.get('dob'):
        dob = datetime.strptime(user['dob'], '%Y-%m-%d')
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    else:
        age = None

    return render_template('home.html', user=user, age=age)

@app.route('/save_notes', methods=['POST'])
def save_notes():
    if 'email' not in session:
        return redirect(url_for('login'))

    notes = request.form['notes']
    users.update_one(
        {'email': session['email']},
        {'$set': {'notes': notes}}  # Update the user's notes
    )

    flash('Notes saved successfully!')
    return redirect(url_for('home'))

# POST method for logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('email', None)
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

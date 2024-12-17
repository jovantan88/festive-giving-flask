from flask import Flask, request, render_template, jsonify, flash, session, redirect, url_for
from functools import wraps
from supabase import create_client
import os
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')
supabase = create_client(supabase_url, supabase_key)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = supabase.auth.get_user()
        if response == None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# @app.route('/data')
# def get_data():
#     # get the table data from supabase
#     response = response = supabase.table("countries").select("*").execute()

#     return jsonify(response)

# @app.route('/add_data')
# def add_data():
#     response = (supabase.table("Test").insert({"created_at": "2024-12-17 05:32:03+00", "test": "Denmark", "cost": "31"}).execute())
#     return jsonify(response)
@app.route('/user/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@app.route('/user/signup', methods=['POST'])
def signup_post():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')

    if not email or not password or not username:
        flash("Missing fields. Please fill all required details.")
        return jsonify({"error": "Invalid request data"}), 400

    try:
        # Sign up the user with Supabase
        response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"username": username, "role": "user"}},
            }
        )
        print("Signup response:", response)
        # Access user ID from the AuthResponse object
        user = response.user  # AuthResponse object has a 'user' attribute
        print("User:", user)
        if user:
            print("User signed up successfully:", user)
            user_id = user.id
            session['user_id'] = user_id
            print(user_id)

            flash("Signed up successfully. Please check your email to confirm your account and login again.")
            return jsonify({"message": "Signed up successfully", "redirect": "/login"}), 200
        else:
            print("Sign-up failed.")
            flash("Sign-up failed. Please try again.")
            return jsonify({"error": "Sign-up failed"}), 400

    except Exception as e:
        print("Error during signup:", e)
        flash("Error signing up. Please try again.")
        return jsonify({"error": "Error signing up"}), 400

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            flash("Missing email or password.")
            return jsonify({"error": "Invalid request data"}), 400

        try:
            response = supabase.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password
                }
            )

            supabase_session = response.session
            session['user_id'] = response.user.id

            flash("Logged in successfully.")
            return jsonify({"message": "Logged in successfully", "redirect": "/home"}), 200
        
        except Exception as e:
            print("Error during login:", e)
            flash("Invalid credentials or error logging in.")
            return jsonify({"error": "Invalid credentials or error logging in"}), 400


@app.route('/home')
@login_required
def home():
    return render_template('home.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')

    elif request.method == 'POST':
        data = request.json
        email = data.get('email')
        if not email:
            flash("Please enter your email.")
            return jsonify({"error": "Email is required"}), 400

        try:
            # Trigger Supabase password reset email
            supabase.auth.reset_password_for_email(email)
            flash("Password reset email sent.")
            return jsonify({"message": "Password reset email sent"}), 200

        except Exception as e:
            print("Error during password reset:", e)
            flash("Error sending password reset email.")
            return jsonify({"error": "Error sending password reset email"}), 400


@app.route('/resend_confirmation', methods=['POST'])
def resend_confirmation():
    data = request.json
    email = data.get('email')

    if not email:
        flash("Email is required to resend confirmation.")
        return jsonify({"error": "Email is required"}), 400

    try:
        # Supabase doesn't have a direct 'resend' function, 
        # but you can re-trigger the sign_up or specific email verification flow if available
        supabase.auth.sign_up(
            {
                "email": email,
                "password": "TEMPORARY_DUMMY_PASSWORD_FOR_RESEND"
            }
        )
        flash("Confirmation email resent. Please check your inbox.")
        return jsonify({"message": "Confirmation email resent"}), 200

    except Exception as e:
        print("Error resending confirmation email:", e)
        flash("Error resending confirmation email.")
        return jsonify({"error": "Error resending confirmation email"}), 400


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    try:
        # Sign out the user
        response = supabase.auth.sign_out()
        session.clear()
        return render_template('login.html')
    except:
        return jsonify({"error": "Error logging out"}), 400
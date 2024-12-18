from flask import Flask, request, render_template, jsonify, flash, session, redirect, url_for
from functools import wraps
from supabase import create_client
from werkzeug.utils import secure_filename
import os
import uuid
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

@app.route('/profile/<username>')
@login_required
def profile(username):
    try:
        user = supabase.auth.get_user()
        
        if user and user.user and user.user.user_metadata:
            current_user = user.user.user_metadata.get('username')
            
            if current_user == username:
                return render_template('profile.html', username=username)
            else:
                flash("You can only view your own profile.")
                return redirect(url_for('home'))
        else:
            flash("Unable to retrieve user information.")
            return redirect(url_for('home'))
    
    except Exception as e:
        print(f"Error retrieving user profile: {e}")
        flash("An error occurred while retrieving the profile.")
        return redirect(url_for('home'))

@app.route('/my_profile')
@login_required
def my_profile():
    try:
        user = supabase.auth.get_user()
        
        if user and user.user and user.user.user_metadata:
            username = user.user.user_metadata.get('username')
            return redirect(url_for('profile', username=username))
        else:
            flash("Unable to retrieve user information.")
            return redirect(url_for('home'))
    
    except Exception as e:
        print(f"Error retrieving user profile: {e}")
        flash("An error occurred while retrieving the profile.")
        return redirect(url_for('home'))

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
    
@app.route('/map', methods=['GET'])
@login_required
def map():
    return render_template('map.html')

@app.route('/add_post', methods=['POST'])
@login_required
def add_post():
    try:
        # Retrieve form data
        caption = request.form.get('caption')
        location_name = request.form.get('location_name')
        
        # TODO: Implement geocoding based on location_name to get location_address and coordinates
        location_address = "Placeholder Address"  # Replace with actual address if available
        coordinates = "213123,3123131"  # Replace with actual coordinates if available

        # Handle image uploads
        images = request.files.getlist('images')
        image_filenames = []
        print("Images:", images)
        for image in images:
            print("Image:", image)
            if image:
                # Secure the filename
                file_name = secure_filename(image.filename)
                
                # Read the file content as bytes
                file_content = image.read()
                print(f'file_name: {file_name}')
                random_id = uuid.uuid1()
                
                response = supabase.storage.from_('Post_images').upload(
                    path=f'images/{random_id}.jpeg',          # path
                    file=file_content,                   # file as bytes
                    file_options={"content-type": "image/jpeg"}
                )
                print("Upload response:", response)
                image_filenames.append(f'images/{random_id}.jpeg')
        print('uploading')
        # Construct the payload for the Supabase table
        new_post = {
            "user_id": str(session.get('user_id')),  # Ensure 'user_id' is set in session upon login
            "image": str(image_filenames),
            "caption": str(caption),
            "location_address": str(location_address),
            "location_name": str(location_name),
            "coordinates": str(coordinates),
            "type": 'Event'  # Adjust the type as needed
        }

        print(f'new_post: {new_post}')

        # Insert into Supabase
        insert_response = supabase.table('posts').insert(new_post).execute()
        return jsonify({"message": "Post added successfully"}), 201

    except Exception as e:
        print("Error in add_post:", e)
        return jsonify({"error": str(e)}), 500

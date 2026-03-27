from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_connection
import hashlib
import random
import string
import os
import time
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'campusconnect_secret_2024'

# ================================
# UPLOAD CONFIGURATION
# ================================
UPLOAD_FOLDER      = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, folder):
    if file and file.filename and allowed_file(file.filename):
        filename  = secure_filename(file.filename)
        filename  = str(int(time.time())) + '_' + filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        return filename
    return None

# ================================
# EMAIL CONFIGURATION
# ================================
MAIL_SERVER   = 'smtp.gmail.com'
MAIL_PORT     = 587
MAIL_USERNAME = 'campusconnect.noreplygmail@gmail.com'
MAIL_PASSWORD = 'fmgginvcvkjipcbk'
MAIL_FROM     = 'CampusConnect <campusconnect.noreplygmail@gmail.com>'

# ================================
# HELPER FUNCTIONS
# ================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_logged_in():
    return 'user_id' in session

def get_unread_count():
    if not is_logged_in():
        return 0
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM MESSAGES
            WHERE receiver_id = :1 AND is_read = 0
        """, (session['user_id'],))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except:
        return 0

def is_valid_comsats_email(email):
    email = email.lower().strip()
    allowed_domains = [
        '@comsats.edu.pk',
        '@student.comsats.edu.pk',
        '@ciit.edu.pk',
        '@students.ciit.edu.pk',
        '@isbstudent.comsats.edu.pk',
        '@isb.student.comsats.edu.pk',
        '@lhr.student.comsats.edu.pk',
        '@khi.student.comsats.edu.pk',
        '@wah.student.comsats.edu.pk',
        '@attd.student.comsats.edu.pk',
        '@sahiwal.student.comsats.edu.pk',
        '@vcast.student.comsats.edu.pk',
        '@gmail.com',
    ]
    for domain in allowed_domains:
        if email.endswith(domain):
            return True
    return False

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(to_email, otp, full_name):
    try:
        msg            = MIMEMultipart('alternative')
        msg['Subject'] = f'CampusConnect - Your OTP is {otp}'
        msg['From']    = MAIL_FROM
        msg['To']      = to_email

        text_body = f"""
CampusConnect - Email Verification
Hello {full_name},
Your OTP verification code is: {otp}
This OTP expires in 10 minutes.
        """
        html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;">
    <div style="max-width:600px;margin:30px auto;background:white;border-radius:12px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#4F46E5,#7C3AED);color:white;padding:30px;text-align:center;">
            <h1>CampusConnect</h1>
        </div>
        <div style="padding:40px;text-align:center;">
            <h2>Hello {full_name}!</h2>
            <p>Your OTP verification code:</p>
            <div style="background:#EEF2FF;border:2px dashed #4F46E5;border-radius:12px;padding:25px;margin:20px auto;display:inline-block;">
                <p style="font-size:44px;font-weight:900;color:#4F46E5;letter-spacing:12px;margin:0;font-family:monospace;">{otp}</p>
            </div>
            <p style="color:#EF4444;font-weight:bold;">Expires in 10 minutes</p>
        </div>
        <div style="background:#f8f9fa;padding:20px;text-align:center;font-size:12px;color:#888;">
            <p>Never share this OTP with anyone.</p>
        </div>
    </div>
</body>
</html>
        """
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Use SSL on port 465 instead of TLS on 587
        import smtplib, ssl
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, to_email, msg.as_string())

        print("Email sent successfully!")
        return True

    except Exception as e:
        print(f"Email Error: {e}")
        return False

def send_welcome_email(to_email, full_name):
    try:
        msg            = MIMEMultipart('alternative')
        msg['Subject'] = 'Welcome to CampusConnect!'
        msg['From']    = MAIL_FROM
        msg['To']      = to_email
        html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;">
    <div style="max-width:600px;margin:30px auto;background:white;border-radius:12px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#4F46E5,#7C3AED);color:white;padding:30px;text-align:center;">
            <h1>Welcome to CampusConnect!</h1>
        </div>
        <div style="padding:30px;">
            <h2>Hello, {full_name}!</h2>
            <p>Your account is verified. You can now access all features!</p>
            <div style="text-align:center;margin-top:20px;">
                <a href="https://your-railway-url.up.railway.app/login"
                   style="background:#4F46E5;color:white;padding:12px 30px;border-radius:8px;text-decoration:none;">
                    Login Now
                </a>
            </div>
        </div>
    </div>
</body>
</html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        import smtplib, ssl
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Welcome email error: {e}")
        return False

# ================================
# HOME
# ================================
@app.route('/')
def home():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ================================
# REGISTER
# ================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        full_name        = request.form['full_name'].strip()
        email            = request.form['email'].strip().lower()
        password         = request.form['password']
        confirm_password = request.form['confirm_password']

        if not full_name or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('register.html')
        if len(full_name) < 3:
            flash('Full name must be at least 3 characters!', 'error')
            return render_template('register.html')
        if not is_valid_comsats_email(email):
            flash('Only COMSATS University email addresses are allowed!', 'error')
            return render_template('register.html')
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('register.html')

        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM USERS WHERE email = :1", (email,))
            if cursor.fetchone()[0] > 0:
                flash('This email is already registered!', 'error')
                cursor.close()
                conn.close()
                return render_template('register.html')
            cursor.close()
            conn.close()

            otp        = generate_otp()
            otp_expiry = datetime.now() + timedelta(minutes=10)
            session['pending_registration'] = {
                'full_name' : full_name,
                'email'     : email,
                'password'  : hash_password(password),
                'otp'       : otp,
                'otp_expiry': otp_expiry.strftime('%Y-%m-%d %H:%M:%S')
            }
            if send_otp_email(email, otp, full_name):
                flash(f'OTP sent to {email}! Check your inbox.', 'success')
                return redirect(url_for('verify_otp'))
            else:
                flash('Failed to send OTP. Please try again.', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('register.html')

# ================================
# VERIFY OTP
# ================================
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_registration' not in session:
        flash('Please register first!', 'error')
        return redirect(url_for('register'))

    pending = session['pending_registration']

    if request.method == 'POST':
        action = request.form.get('action', 'verify')

        if action == 'resend':
            new_otp    = generate_otp()
            new_expiry = datetime.now() + timedelta(minutes=10)

            session['pending_registration']['otp']        = new_otp
            session['pending_registration']['otp_expiry'] = new_expiry.strftime('%Y-%m-%d %H:%M:%S')
            session.modified = True

            if send_otp_email(pending['email'], new_otp, pending['full_name']):
                flash('New OTP sent!', 'success')
            else:
                flash('Failed to resend OTP.', 'error')

            return render_template('verify_otp.html', email=pending['email'])

        entered_otp = request.form.get('otp', '').strip()
        expiry      = datetime.strptime(pending['otp_expiry'], '%Y-%m-%d %H:%M:%S')

        if datetime.now() > expiry:
            flash('OTP has expired! Request a new one.', 'error')
            return render_template('verify_otp.html', email=pending['email'])

        if entered_otp != pending['otp']:
            flash('Invalid OTP! Please try again.', 'error')
            return render_template('verify_otp.html', email=pending['email'])

        try:
            conn   = get_connection()
            cursor = conn.cursor()

            # ✅ INSERT USER (NO ID)
            cursor.execute("""
                INSERT INTO USERS (full_name, email, password, university)
                VALUES (:1, :2, :3, 'COMSATS University Islamabad')
            """, (pending['full_name'], pending['email'], pending['password']))

            conn.commit()

            # ✅ GET USER ID
            cursor.execute("SELECT user_id FROM USERS WHERE email = :1", (pending['email'],))
            new_user = cursor.fetchone()

            if new_user:
                # ✅ FIXED NOTIFICATION INSERT (NO notif_id)
                cursor.execute("""
                    INSERT INTO NOTIFICATIONS
                    (user_id, title, message, notif_type)
                    VALUES (:1, :2, :3, 'general')
                """, (
                    new_user[0],
                    'Welcome to CampusConnect!',
                    'Your account is verified. Start exploring!'
                ))

                conn.commit()

            cursor.close()
            conn.close()

            send_welcome_email(pending['email'], pending['full_name'])
            session.pop('pending_registration', None)

            flash('Email verified! Welcome to CampusConnect!', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    return render_template('verify_otp.html', email=pending['email'])
# ================================
# LOGIN
# ================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form['email'].strip().lower()
        password = request.form['password']
        hashed   = hash_password(password)
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, full_name, email, university
                FROM USERS WHERE email = :1 AND password = :2
            """, (email, hashed))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                session['user_id']    = user[0]
                session['full_name']  = user[1]
                session['email']      = user[2]
                session['university'] = user[3]
                flash(f'Welcome back, {user[1]}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password!', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('login.html')

# ================================
# LOGOUT
# ================================
@app.route('/logout')
def logout():
    name = session.get('full_name', '')
    session.clear()
    flash(f'Goodbye, {name}! See you soon.', 'success')
    return redirect(url_for('login'))

# ================================
# DASHBOARD
# ================================
@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.ride_id, r.from_location, r.to_location,
                   r.ride_date, r.ride_time, r.seats_available,
                   r.price_per_seat, u.full_name
            FROM RIDES r JOIN USERS u ON r.user_id = u.user_id
            WHERE r.status = 'active'
            ORDER BY r.created_at DESC
            FETCH FIRST 3 ROWS ONLY
        """)
        rides = cursor.fetchall()
        cursor.execute("""
            SELECT h.hostel_id, h.name, h.location,
                   h.price, h.gender, h.facilities
            FROM HOSTELS h
            ORDER BY h.created_at DESC
            FETCH FIRST 3 ROWS ONLY
        """)
        hostels = cursor.fetchall()
        cursor.execute("""
            SELECT m.item_id, m.title, m.price,
                   m.category, m.condition, u.full_name
            FROM MARKETPLACE m JOIN USERS u ON m.user_id = u.user_id
            WHERE m.status = 'available'
            ORDER BY m.created_at DESC
            FETCH FIRST 4 ROWS ONLY
        """)
        items = cursor.fetchall()
        cursor.execute("""
            SELECT COUNT(*) FROM MESSAGES
            WHERE receiver_id = :1 AND is_read = 0
        """, (session['user_id'],))
        unread = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM RIDES WHERE status='active'")
        total_rides = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM HOSTELS")
        total_hostels = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM MARKETPLACE WHERE status='available'")
        total_items = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM USERS")
        total_users = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return render_template('dashboard.html',
                             rides=rides, hostels=hostels,
                             items=items, unread=unread,
                             total_rides=total_rides,
                             total_hostels=total_hostels,
                             total_items=total_items,
                             total_users=total_users)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('dashboard.html',
                             rides=[], hostels=[], items=[],
                             unread=0, total_rides=0,
                             total_hostels=0, total_items=0,
                             total_users=0)

# ================================
# RIDES
# ================================
@app.route('/rides')
def rides():
    if not is_logged_in():
        return redirect(url_for('login'))
    search = request.args.get('search', '')
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        if search:
            cursor.execute("""
                SELECT r.ride_id, r.from_location, r.to_location,
                       r.ride_date, r.ride_time, r.seats_available,
                       r.price_per_seat, u.full_name, u.user_id,
                       r.pickup_lat, r.pickup_lng,
                       r.dropoff_lat, r.dropoff_lng
                FROM RIDES r JOIN USERS u ON r.user_id = u.user_id
                WHERE r.status = 'active'
                AND (LOWER(r.from_location) LIKE :1
                OR LOWER(r.to_location) LIKE :1)
                ORDER BY r.ride_date ASC
            """, (f'%{search.lower()}%',))
        else:
            cursor.execute("""
                SELECT r.ride_id, r.from_location, r.to_location,
                       r.ride_date, r.ride_time, r.seats_available,
                       r.price_per_seat, u.full_name, u.user_id,
                       r.pickup_lat, r.pickup_lng,
                       r.dropoff_lat, r.dropoff_lng
                FROM RIDES r JOIN USERS u ON r.user_id = u.user_id
                WHERE r.status = 'active'
                ORDER BY r.ride_date ASC
            """)
        rides  = cursor.fetchall()
        unread = get_unread_count()
        cursor.close()
        conn.close()
        return render_template('rides.html',
                             rides=rides, search=search, unread=unread)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('rides.html', rides=[], search='', unread=0)

@app.route('/rides/post', methods=['GET', 'POST'])
def post_ride():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            pickup_lat  = request.form.get('pickup_lat')  or None
            pickup_lng  = request.form.get('pickup_lng')  or None
            dropoff_lat = request.form.get('dropoff_lat') or None
            dropoff_lng = request.form.get('dropoff_lng') or None
            distance_km = request.form.get('distance_km') or None
            duration_mn = request.form.get('duration_mins') or None
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO RIDES (
                    user_id, from_location, to_location,
                    ride_date, ride_time, seats_available,
                    price_per_seat, pickup_lat, pickup_lng,
                    dropoff_lat, dropoff_lng,
                    distance_km, duration_mins
                ) VALUES (
                    :1, :2, :3,
                    TO_DATE(:4, 'YYYY-MM-DD'), :5, :6,
                    :7, :8, :9, :10, :11, :12, :13
                )
            """, (
                session['user_id'],
                request.form['from_location'],
                request.form['to_location'],
                request.form['ride_date'],
                request.form['ride_time'],
                int(request.form['seats']),
                float(request.form['price']),
                float(pickup_lat)  if pickup_lat  else None,
                float(pickup_lng)  if pickup_lng  else None,
                float(dropoff_lat) if dropoff_lat else None,
                float(dropoff_lng) if dropoff_lng else None,
                float(distance_km) if distance_km else None,
                int(duration_mn)   if duration_mn else None
            ))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Ride posted successfully!', 'success')
            return redirect(url_for('rides'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('post_ride.html', unread=get_unread_count())

@app.route('/rides/<int:ride_id>')
def ride_detail(ride_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.ride_id, r.from_location, r.to_location,
                   r.ride_date, r.ride_time, r.seats_available,
                   r.price_per_seat, r.pickup_lat, r.pickup_lng,
                   r.dropoff_lat, r.dropoff_lng,
                   r.distance_km, r.duration_mins,
                   r.status, u.full_name, u.email, u.user_id
            FROM RIDES r JOIN USERS u ON r.user_id = u.user_id
            WHERE r.ride_id = :1
        """, (ride_id,))
        ride = cursor.fetchone()
        cursor.execute("""
            SELECT u.full_name, rr.status, rr.created_at, u.user_id
            FROM RIDE_REQUESTS rr
            JOIN USERS u ON rr.user_id = u.user_id
            WHERE rr.ride_id = :1
        """, (ride_id,))
        requests = cursor.fetchall()
        cursor.execute("""
            SELECT COUNT(*) FROM RIDE_REQUESTS
            WHERE ride_id = :1 AND user_id = :2
        """, (ride_id, session['user_id']))
        already_requested = cursor.fetchone()[0] > 0
        cursor.execute("""
            SELECT u.full_name, rv.rating, rv.comments
            FROM REVIEWS rv
            JOIN USERS u ON rv.reviewer_id = u.user_id
            WHERE rv.target_type = 'RIDE'
            AND rv.target_id = :1
            ORDER BY rv.created_at DESC
        """, (ride_id,))
        reviews = cursor.fetchall()
        unread  = get_unread_count()
        cursor.close()
        conn.close()
        return render_template('ride_detail.html',
                             ride=ride, requests=requests,
                             already_requested=already_requested,
                             reviews=reviews, unread=unread)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('rides'))

@app.route('/rides/request/<int:ride_id>')
def request_ride(ride_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO RIDE_REQUESTS (ride_id, user_id)
            VALUES (:1, :2)
        """, (ride_id, session['user_id']))
        conn.commit()
        cursor.execute("""
            SELECT user_id, from_location, to_location
            FROM RIDES WHERE ride_id = :1
        """, (ride_id,))
        ride_info = cursor.fetchone()
        if ride_info:
            cursor.execute("""
                INSERT INTO NOTIFICATIONS
                (notif_id, user_id, title, message, notif_type)
                VALUES (notif_seq.NEXTVAL, :1, :2, :3, 'ride_request')
            """, (ride_info[0], 'New Ride Request!',
                  f'{session["full_name"]} requested a seat on your ride.'))
            conn.commit()
        cursor.close()
        conn.close()
        flash('Ride request sent!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('ride_detail', ride_id=ride_id))

@app.route('/rides/accept/<int:ride_id>/<int:user_id>')
def accept_ride(ride_id, user_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.callproc('accept_ride_request',
                       [ride_id, user_id, session['user_id']])
        conn.commit()
        cursor.close()
        conn.close()
        flash('Ride request accepted!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('ride_detail', ride_id=ride_id))

@app.route('/rides/reject/<int:ride_id>/<int:user_id>')
def reject_ride(ride_id, user_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.callproc('reject_ride_request', [ride_id, user_id])
        conn.commit()
        cursor.close()
        conn.close()
        flash('Ride request rejected!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('ride_detail', ride_id=ride_id))

@app.route('/rides/delete/<int:ride_id>')
def delete_ride(ride_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.callproc('cancel_ride_notify',
                       [ride_id, session['user_id']])
        conn.commit()
        cursor.close()
        conn.close()
        flash('Ride cancelled!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('profile'))

# ================================
# HOSTELS
# ================================
@app.route('/hostels')
def hostels():
    if not is_logged_in():
        return redirect(url_for('login'))
    search = request.args.get('search', '')
    gender = request.args.get('gender', '')
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        if search and gender:
            cursor.execute("""
                SELECT h.hostel_id, h.name, h.location, h.price,
                       h.gender, h.facilities, h.contact, u.full_name
                FROM HOSTELS h JOIN USERS u ON h.user_id = u.user_id
                WHERE (LOWER(h.name) LIKE :1
                OR LOWER(h.location) LIKE :1)
                AND h.gender = :2
                ORDER BY h.created_at DESC
            """, (f'%{search.lower()}%', gender))
        elif search:
            cursor.execute("""
                SELECT h.hostel_id, h.name, h.location, h.price,
                       h.gender, h.facilities, h.contact, u.full_name
                FROM HOSTELS h JOIN USERS u ON h.user_id = u.user_id
                WHERE LOWER(h.name) LIKE :1
                OR LOWER(h.location) LIKE :1
                ORDER BY h.created_at DESC
            """, (f'%{search.lower()}%',))
        elif gender:
            cursor.execute("""
                SELECT h.hostel_id, h.name, h.location, h.price,
                       h.gender, h.facilities, h.contact, u.full_name
                FROM HOSTELS h JOIN USERS u ON h.user_id = u.user_id
                WHERE h.gender = :1
                ORDER BY h.created_at DESC
            """, (gender,))
        else:
            cursor.execute("""
                SELECT h.hostel_id, h.name, h.location, h.price,
                       h.gender, h.facilities, h.contact, u.full_name
                FROM HOSTELS h JOIN USERS u ON h.user_id = u.user_id
                ORDER BY h.created_at DESC
            """)
        hostels = cursor.fetchall()
        unread  = get_unread_count()
        cursor.close()
        conn.close()
        return render_template('hostels.html',
                             hostels=hostels, search=search,
                             gender=gender, unread=unread)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('hostels.html',
                             hostels=[], search='', gender='', unread=0)

@app.route('/hostels/post', methods=['GET', 'POST'])
def post_hostel():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            image_filename = None
            if 'image' in request.files:
                image_filename = save_image(request.files['image'], 'hostels')
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO HOSTELS
                (user_id, name, location, price, gender, facilities, contact)
                VALUES (:1, :2, :3, :4, :5, :6, :7)
            """, (
                session['user_id'],
                request.form['name'],
                request.form['location'],
                float(request.form['price']),
                request.form['gender'],
                request.form['facilities'],
                request.form['contact']
            ))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Hostel listed successfully!', 'success')
            return redirect(url_for('hostels'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('post_hostel.html', unread=get_unread_count())

@app.route('/hostels/<int:hostel_id>')
def hostel_detail(hostel_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT h.hostel_id, h.name, h.location, h.price,
                   h.gender, h.facilities, h.contact,
                   u.full_name, u.email, u.user_id
            FROM HOSTELS h JOIN USERS u ON h.user_id = u.user_id
            WHERE h.hostel_id = :1
        """, (hostel_id,))
        hostel = cursor.fetchone()
        cursor.execute("""
            SELECT COUNT(*) FROM HOSTEL_BOOKMARKS
            WHERE user_id = :1 AND hostel_id = :2
        """, (session['user_id'], hostel_id))
        is_bookmarked = cursor.fetchone()[0] > 0
        cursor.execute("""
            SELECT u.full_name, rv.rating, rv.comments
            FROM REVIEWS rv
            JOIN USERS u ON rv.reviewer_id = u.user_id
            WHERE rv.target_type = 'HOSTEL'
            AND rv.target_id = :1
            ORDER BY rv.created_at DESC
        """, (hostel_id,))
        reviews = cursor.fetchall()
        unread  = get_unread_count()
        cursor.close()
        conn.close()
        return render_template('hostel_detail.html',
                             hostel=hostel,
                             is_bookmarked=is_bookmarked,
                             reviews=reviews,
                             unread=unread)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('hostels'))

@app.route('/hostels/bookmark/<int:hostel_id>')
def bookmark_hostel(hostel_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        action = cursor.var(str)
        cursor.callproc('toggle_bookmark',
                       [session['user_id'], hostel_id, action])
        conn.commit()
        cursor.close()
        conn.close()
        if action.getvalue() == 'added':
            flash('Hostel bookmarked!', 'success')
        else:
            flash('Bookmark removed!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('hostel_detail', hostel_id=hostel_id))

@app.route('/hostels/delete/<int:hostel_id>')
def delete_hostel(hostel_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM HOSTELS
            WHERE hostel_id = :1 AND user_id = :2
        """, (hostel_id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Hostel listing removed!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('profile'))

# ================================
# MARKETPLACE
# ================================
@app.route('/marketplace')
def marketplace():
    if not is_logged_in():
        return redirect(url_for('login'))
    search   = request.args.get('search', '')
    category = request.args.get('category', '')
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        if search and category:
            cursor.execute("""
                SELECT m.item_id, m.title, m.description, m.price,
                       m.category, m.condition, u.full_name, u.user_id
                FROM MARKETPLACE m JOIN USERS u ON m.user_id = u.user_id
                WHERE m.status = 'available'
                AND (LOWER(m.title) LIKE :1
                OR LOWER(m.description) LIKE :1)
                AND m.category = :2
                ORDER BY m.created_at DESC
            """, (f'%{search.lower()}%', category))
        elif search:
            cursor.execute("""
                SELECT m.item_id, m.title, m.description, m.price,
                       m.category, m.condition, u.full_name, u.user_id
                FROM MARKETPLACE m JOIN USERS u ON m.user_id = u.user_id
                WHERE m.status = 'available'
                AND (LOWER(m.title) LIKE :1
                OR LOWER(m.description) LIKE :1)
                ORDER BY m.created_at DESC
            """, (f'%{search.lower()}%',))
        elif category:
            cursor.execute("""
                SELECT m.item_id, m.title, m.description, m.price,
                       m.category, m.condition, u.full_name, u.user_id
                FROM MARKETPLACE m JOIN USERS u ON m.user_id = u.user_id
                WHERE m.status = 'available'
                AND m.category = :1
                ORDER BY m.created_at DESC
            """, (category,))
        else:
            cursor.execute("""
                SELECT m.item_id, m.title, m.description, m.price,
                       m.category, m.condition, u.full_name, u.user_id
                FROM MARKETPLACE m JOIN USERS u ON m.user_id = u.user_id
                WHERE m.status = 'available'
                ORDER BY m.created_at DESC
            """)
        items  = cursor.fetchall()
        unread = get_unread_count()
        cursor.close()
        conn.close()
        return render_template('marketplace.html',
                             items=items, search=search,
                             category=category, unread=unread)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('marketplace.html',
                             items=[], search='', category='', unread=0)

@app.route('/marketplace/post', methods=['GET', 'POST'])
def post_item():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            image_filename = None
            if 'image' in request.files:
                image_filename = save_image(
                    request.files['image'], 'marketplace')
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO MARKETPLACE
                (user_id, title, description, price, category, condition)
                VALUES (:1, :2, :3, :4, :5, :6)
            """, (
                session['user_id'],
                request.form['title'],
                request.form['description'],
                float(request.form['price']),
                request.form['category'],
                request.form['condition']
            ))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Item listed successfully!', 'success')
            return redirect(url_for('marketplace'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('post_item.html', unread=get_unread_count())

@app.route('/marketplace/<int:item_id>')
def item_detail(item_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.item_id, m.title, m.description, m.price,
                   m.category, m.condition, m.status,
                   u.full_name, u.email, u.user_id
            FROM MARKETPLACE m JOIN USERS u ON m.user_id = u.user_id
            WHERE m.item_id = :1
        """, (item_id,))
        item   = cursor.fetchone()
        unread = get_unread_count()
        cursor.close()
        conn.close()
        return render_template('item_detail.html',
                             item=item, unread=unread)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('marketplace'))

@app.route('/marketplace/delete/<int:item_id>')
def delete_item(item_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE MARKETPLACE SET status = 'sold'
            WHERE item_id = :1 AND user_id = :2
        """, (item_id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Item marked as sold!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('profile'))

@app.route('/marketplace/report/<int:item_id>', methods=['POST'])
def report_item(item_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.callproc('report_marketplace_item', [
            session['user_id'],
            item_id,
            request.form.get('reason', 'Suspicious listing')
        ])
        conn.commit()
        cursor.close()
        conn.close()
        flash('Item reported successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('item_detail', item_id=item_id))

# ================================
# REVIEWS
# ================================
@app.route('/reviews/add', methods=['POST'])
def add_review():
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.callproc('add_review', [
            session['user_id'],
            request.form['target_type'],
            int(request.form['target_id']),
            int(request.form['rating']),
            request.form.get('comment', '')
        ])
        conn.commit()
        cursor.close()
        conn.close()
        flash('Review submitted!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(request.referrer or url_for('dashboard'))

# ================================
# MESSAGES
# ================================
@app.route('/messages')
def messages():
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        uid    = session['user_id']
        cursor.execute("""
            SELECT DISTINCT sender_id FROM MESSAGES
            WHERE receiver_id = :1
            UNION
            SELECT DISTINCT receiver_id FROM MESSAGES
            WHERE sender_id = :2
        """, (uid, uid))
        other_ids     = [row[0] for row in cursor.fetchall()]
        conversations = []
        for other_id in other_ids:
            cursor.execute("""
                SELECT full_name FROM USERS WHERE user_id = :1
            """, (other_id,))
            user_row = cursor.fetchone()
            if not user_row:
                continue
            cursor.execute("""
                SELECT MAX(created_at) FROM MESSAGES
                WHERE (sender_id = :1 AND receiver_id = :2)
                OR (sender_id = :2 AND receiver_id = :1)
            """, (uid, other_id))
            last_time = cursor.fetchone()[0]
            conversations.append((other_id, user_row[0], last_time))
        conversations.sort(
            key=lambda x: x[2] if x[2] else datetime.min,
            reverse=True
        )
        unread = get_unread_count()
        cursor.close()
        conn.close()
        return render_template('messages.html',
                             conversations=conversations,
                             unread=unread)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('messages.html',
                             conversations=[], unread=0)

@app.route('/messages/<int:other_id>', methods=['GET', 'POST'])
def chat(other_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        message = request.form['message'].strip()
        if message:
            try:
                conn   = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO MESSAGES (sender_id, receiver_id, message)
                    VALUES (:1, :2, :3)
                """, (session['user_id'], other_id, message))
                cursor.execute("""
                    INSERT INTO NOTIFICATIONS
                    (notif_id, user_id, title, message, notif_type)
                    VALUES (notif_seq.NEXTVAL, :1, :2, :3, 'message')
                """, (other_id, 'New Message!',
                      f'You have a new message from {session["full_name"]}'))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE MESSAGES SET is_read = 1
            WHERE sender_id = :1 AND receiver_id = :2
        """, (other_id, session['user_id']))
        conn.commit()
        cursor.execute("""
            SELECT m.message, m.sender_id, m.created_at, u.full_name
            FROM MESSAGES m JOIN USERS u ON m.sender_id = u.user_id
            WHERE (m.sender_id = :1 AND m.receiver_id = :2)
            OR    (m.sender_id = :2 AND m.receiver_id = :1)
            ORDER BY m.created_at ASC
        """, (session['user_id'], other_id))
        chats = cursor.fetchall()
        cursor.execute("""
            SELECT full_name, email FROM USERS WHERE user_id = :1
        """, (other_id,))
        other_user = cursor.fetchone()
        unread     = get_unread_count()
        cursor.close()
        conn.close()
        return render_template('chat.html',
                             chats=chats, other_user=other_user,
                             other_id=other_id, unread=unread)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('messages'))

# ================================
# NOTIFICATIONS
# ================================
@app.route('/notifications')
def notifications():
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT notif_id, title, message,
                   notif_type, is_read, created_at
            FROM NOTIFICATIONS
            WHERE user_id = :1
            ORDER BY created_at DESC
        """, (session['user_id'],))
        notifs = cursor.fetchall()
        cursor.callproc('mark_notifications_read', [session['user_id']])
        conn.commit()
        cursor.close()
        conn.close()
        return render_template('notifications.html',
                             notifs=notifs, unread=0)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('notifications.html',
                             notifs=[], unread=0)

# ================================
# GLOBAL SEARCH
# ================================
@app.route('/search')
def global_search():
    if not is_logged_in():
        return redirect(url_for('login'))
    keyword = request.args.get('q', '')
    results = {'rides': [], 'hostels': [], 'items': []}
    if keyword:
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.ride_id, r.from_location, r.to_location,
                       r.ride_date, r.ride_time, r.seats_available,
                       r.price_per_seat, u.full_name
                FROM RIDES r JOIN USERS u ON r.user_id = u.user_id
                WHERE r.status = 'active'
                AND (LOWER(r.from_location) LIKE :1
                OR LOWER(r.to_location) LIKE :1)
            """, (f'%{keyword.lower()}%',))
            results['rides'] = cursor.fetchall()
            cursor.execute("""
                SELECT h.hostel_id, h.name, h.location,
                       h.price, h.gender, h.facilities
                FROM HOSTELS h
                WHERE LOWER(h.name) LIKE :1
                OR LOWER(h.location) LIKE :1
            """, (f'%{keyword.lower()}%',))
            results['hostels'] = cursor.fetchall()
            cursor.execute("""
                SELECT m.item_id, m.title, m.price,
                       m.category, m.condition, u.full_name
                FROM MARKETPLACE m
                JOIN USERS u ON m.user_id = u.user_id
                WHERE m.status = 'available'
                AND (LOWER(m.title) LIKE :1
                OR LOWER(m.description) LIKE :1)
            """, (f'%{keyword.lower()}%',))
            results['items'] = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('search_results.html',
                         results=results,
                         keyword=keyword,
                         unread=get_unread_count())

# ================================
# PROFILE
# ================================
@app.route('/profile')
def profile():
    if not is_logged_in():
        return redirect(url_for('login'))
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, full_name, email, university, created_at
            FROM USERS WHERE user_id = :1
        """, (session['user_id'],))
        user = cursor.fetchone()
        cursor.execute("""
            SELECT ride_id, from_location, to_location, ride_date, status
            FROM RIDES WHERE user_id = :1
            ORDER BY created_at DESC
        """, (session['user_id'],))
        my_rides = cursor.fetchall()
        cursor.execute("""
            SELECT item_id, title, price, category, status
            FROM MARKETPLACE WHERE user_id = :1
            ORDER BY created_at DESC
        """, (session['user_id'],))
        my_items = cursor.fetchall()
        cursor.execute("""
            SELECT hostel_id, name, location, price
            FROM HOSTELS WHERE user_id = :1
            ORDER BY created_at DESC
        """, (session['user_id'],))
        my_hostels = cursor.fetchall()
        cursor.execute("""
            SELECT department, semester, roll_no, bio, phone, city
            FROM USER_PROFILES WHERE user_id = :1
        """, (session['user_id'],))
        user_profile = cursor.fetchone()
        unread = get_unread_count()
        cursor.close()
        conn.close()
        return render_template('profile.html',
                             user=user, my_rides=my_rides,
                             my_items=my_items, my_hostels=my_hostels,
                             user_profile=user_profile, unread=unread)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('profile.html',
                             user=None, my_rides=[], my_items=[],
                             my_hostels=[], user_profile=None, unread=0)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            conn   = get_connection()
            cursor = conn.cursor()
            cursor.callproc('save_user_profile', [
                session['user_id'],
                request.form.get('department', ''),
                request.form.get('semester', ''),
                request.form.get('roll_no', ''),
                request.form.get('bio', ''),
                request.form.get('phone', ''),
                request.form.get('city', '')
            ])
            conn.commit()
            cursor.close()
            conn.close()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT department, semester, roll_no, bio, phone, city
            FROM USER_PROFILES WHERE user_id = :1
        """, (session['user_id'],))
        prof   = cursor.fetchone()
        unread = get_unread_count()
        cursor.close()
        conn.close()
        return render_template('edit_profile.html',
                             prof=prof, unread=unread)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('edit_profile.html', prof=None, unread=0)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
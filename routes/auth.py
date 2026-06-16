from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from helpers import hash_password, is_logged_in, is_valid_email
from datetime import datetime, timedelta
from bson import ObjectId
import random, string, smtplib, ssl, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

auth_bp = Blueprint('auth', __name__)

MAIL_USER = os.environ.get('MAIL_USERNAME','campusconnect.noreplygmail@gmail.com')
MAIL_PASS = os.environ.get('MAIL_PASSWORD','')
MAIL_FROM = os.environ.get('MAIL_FROM', 'CampusConnect <noreply@cuiconnect.app>')

def gen_otp():
    return ''.join(random.choices(string.digits, k=6))

def _send_email(to, subject, html):
    """
    Send email via SMTP port 587 (STARTTLS) synchronously.
    On Vercel serverless, daemon threads are killed after the response returns,
    so we MUST send synchronously. Port 587 STARTTLS is used instead of 465 SSL
    because Vercel's outbound firewall sometimes blocks port 465.
    Supports both Gmail and COMSATS Microsoft Office 365 Outlook SMTP automatically.
    """
    if not MAIL_PASS:
        print("Email skipped: MAIL_PASSWORD env var not set.")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = MAIL_FROM
        msg['To'] = to
        msg.attach(MIMEText(html, 'html'))
        ctx = ssl.create_default_context()
        
        # Dynamically determine SMTP host based on sending email
        smtp_host = 'smtp.gmail.com'
        if 'comsats.edu.pk' in MAIL_USER.lower() or 'office365' in MAIL_USER.lower():
            smtp_host = 'smtp.office365.com'
        elif 'brevo' in MAIL_USER.lower() or 'sib' in MAIL_USER.lower():
            smtp_host = 'smtp-relay.brevo.com'
            
        with smtplib.SMTP(smtp_host, 587, timeout=20) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.ehlo()
            s.login(MAIL_USER, MAIL_PASS)
            s.sendmail(MAIL_USER, to, msg.as_string())
        print(f"Email sent OK to {to} via {smtp_host}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# send_async now sends synchronously — Vercel kills threads after response
def send_async(to, subject, html):
    return _send_email(to, subject, html)

def otp_html(name, otp):
    return f"""<body style="font-family:Arial;background:#f4f4f4">
<div style="max-width:600px;margin:30px auto;background:#fff;border-radius:12px;overflow:hidden">
<div style="background:linear-gradient(135deg,#4F46E5,#7C3AED);color:#fff;padding:30px;text-align:center"><h1>CampusConnect</h1></div>
<div style="padding:40px;text-align:center"><h2>Hello {name}!</h2>
<p>Your OTP:</p>
<div style="background:#EEF2FF;border:2px dashed #4F46E5;border-radius:12px;padding:25px;margin:20px auto;display:inline-block">
<p style="font-size:44px;font-weight:900;color:#4F46E5;letter-spacing:12px;margin:0;font-family:monospace">{otp}</p></div>
<p style="color:#EF4444;font-weight:bold">Expires in 10 minutes</p></div></div></body>"""

@auth_bp.route('/')
def home():
    return redirect(url_for('auth.dashboard') if is_logged_in() else url_for('auth.login'))

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if is_logged_in(): return redirect(url_for('auth.dashboard'))
    if request.method == 'POST':
        name  = request.form['full_name'].strip()
        email = request.form['email'].strip().lower()
        pw    = request.form['password']
        cpw   = request.form['confirm_password']
        if not name or not email or not pw:
            flash('All fields required!','error'); return render_template('register.html')
        if len(name) < 3:
            flash('Name too short!','error'); return render_template('register.html')
        if not is_valid_email(email):
            flash('Only COMSATS email addresses allowed!','error'); return render_template('register.html')
        if pw != cpw:
            flash('Passwords do not match!','error'); return render_template('register.html')
        if len(pw) < 6:
            flash('Password min 6 characters!','error'); return render_template('register.html')
            
        db = get_db()
        
        # Get client IP address
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
            
        # Rate Limiting: Max 3 signup attempts per IP or Email per 5 minutes
        five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
        ip_attempts = db.signup_attempts.count_documents({
            'ip': client_ip,
            'created_at': {'$gte': five_mins_ago}
        })
        email_attempts = db.signup_attempts.count_documents({
            'email': email,
            'created_at': {'$gte': five_mins_ago}
        })
        
        if ip_attempts >= 3 or email_attempts >= 3:
            flash('Too many verification requests! Please try again in 5 minutes.', 'error')
            return render_template('register.html')
            
        # Log this attempt
        db.signup_attempts.insert_one({
            'ip': client_ip,
            'email': email,
            'created_at': datetime.utcnow()
        })
        
        if db.users.count_documents({'email':email}) > 0:
            flash('Email already registered!','error'); return render_template('register.html')
        otp = gen_otp()
        session['pending_registration'] = {
            'full_name': name, 'email': email, 'password': hash_password(pw),
            'otp': otp, 'otp_expiry': (datetime.now()+timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        }
        send_async(email, f'CampusConnect OTP: {otp}', otp_html(name, otp))
        flash(f'OTP sent to {email}!','success')
        return redirect(url_for('auth.verify_otp'))
    return render_template('register.html')

@auth_bp.route('/verify-otp', methods=['GET','POST'])
def verify_otp():
    if 'pending_registration' not in session:
        flash('Register first!','error'); return redirect(url_for('auth.register'))
    p = session['pending_registration']
    if request.method == 'POST':
        if request.form.get('action') == 'resend':
            otp = gen_otp()
            session['pending_registration']['otp'] = otp
            session['pending_registration']['otp_expiry'] = (datetime.now()+timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
            session.modified = True
            send_async(p['email'], f'CampusConnect OTP: {otp}', otp_html(p['full_name'], otp))
            flash('New OTP sent!','success')
            return render_template('verify_otp.html', email=p['email'])
        entered = request.form.get('otp','').strip()
        if datetime.now() > datetime.strptime(p['otp_expiry'],'%Y-%m-%d %H:%M:%S'):
            flash('OTP expired!','error'); return render_template('verify_otp.html',email=p['email'])
        if entered != p['otp']:
            flash('Invalid OTP!','error'); return render_template('verify_otp.html',email=p['email'])
        db = get_db()
        res = db.users.insert_one({'full_name':p['full_name'],'email':p['email'],'password':p['password'],
                                   'university':'COMSATS University Islamabad','created_at':datetime.utcnow()})
        db.notifications.insert_one({'user_id':str(res.inserted_id),'title':'Welcome to CampusConnect!',
            'message':'Your account is verified. Start exploring!','notif_type':'general','is_read':False,'created_at':datetime.utcnow()})
        session.pop('pending_registration',None)
        flash('Email verified! Welcome to CampusConnect!','success')
        return redirect(url_for('auth.login'))
    return render_template('verify_otp.html',email=p['email'])

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if is_logged_in(): return redirect(url_for('auth.dashboard'))
    if request.method == 'POST':
        email  = request.form['email'].strip().lower()
        hashed = hash_password(request.form['password'])
        db = get_db()
        user = db.users.find_one({'email':email,'password':hashed})
        if user:
            session['user_id']    = str(user['_id'])
            session['full_name']  = user['full_name']
            session['email']      = user['email']
            session['university'] = user.get('university','COMSATS University Islamabad')
            session['profile_pic'] = user.get('profile_pic', '')
            flash(f"Welcome back, {user['full_name']}!",'success')
            return redirect(url_for('auth.dashboard'))
        flash('Invalid email or password!','error')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    name = session.get('full_name','')
    session.clear()
    flash(f'Goodbye, {name}! See you soon.','success')
    return redirect(url_for('auth.login'))


# ── Forgot Password ────────────────────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if is_logged_in(): return redirect(url_for('auth.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('forgot_password.html')
            
        db = get_db()
        
        # Get client IP address
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
            
        # Rate Limiting: Max 3 password reset attempts per IP or Email per 5 minutes
        five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
        ip_attempts = db.signup_attempts.count_documents({
            'ip': client_ip,
            'created_at': {'$gte': five_mins_ago}
        })
        email_attempts = db.signup_attempts.count_documents({
            'email': email,
            'created_at': {'$gte': five_mins_ago}
        })
        
        if ip_attempts >= 3 or email_attempts >= 3:
            flash('Too many requests! Please try again in 5 minutes.', 'error')
            return render_template('forgot_password.html')
            
        # Log this attempt
        db.signup_attempts.insert_one({
            'ip': client_ip,
            'email': email,
            'created_at': datetime.utcnow()
        })
        user = db.users.find_one({'email': email})
        if not user:
            # Generic message to prevent email enumeration
            flash('If that email is registered, an OTP has been sent.', 'success')
            return render_template('forgot_password.html', sent=True)
        otp = gen_otp()
        session['pending_reset'] = {
            'email': email,
            'otp': otp,
            'otp_expiry': (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        }
        html = f"""<body style="font-family:Arial;background:#f4f4f4">
<div style="max-width:600px;margin:30px auto;background:#fff;border-radius:12px;overflow:hidden">
<div style="background:linear-gradient(135deg,#4F46E5,#7C3AED);color:#fff;padding:30px;text-align:center"><h1>CampusConnect</h1></div>
<div style="padding:40px;text-align:center"><h2>Reset Your Password</h2>
<p>Use this OTP to reset your password:</p>
<div style="background:#EEF2FF;border:2px dashed #4F46E5;border-radius:12px;padding:25px;margin:20px auto;display:inline-block">
<p style="font-size:44px;font-weight:900;color:#4F46E5;letter-spacing:12px;margin:0;font-family:monospace">{otp}</p></div>
<p style="color:#EF4444;font-weight:bold">Expires in 10 minutes</p>
<p style="color:#64748B;font-size:13px">If you did not request this, please ignore this email.</p>
</div></div></body>"""
        send_async(email, f'CampusConnect Password Reset OTP: {otp}', html)
        flash('OTP sent to your email address!', 'success')
        return redirect(url_for('auth.reset_password'))
    return render_template('forgot_password.html')


@auth_bp.route('/reset-password', methods=['GET','POST'])
def reset_password():
    if is_logged_in(): return redirect(url_for('auth.dashboard'))
    if 'pending_reset' not in session:
        flash('Please request a password reset first.', 'error')
        return redirect(url_for('auth.forgot_password'))
    p = session['pending_reset']
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'resend':
            otp = gen_otp()
            session['pending_reset']['otp'] = otp
            session['pending_reset']['otp_expiry'] = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
            session.modified = True
            html = f"""<body style="font-family:Arial;background:#f4f4f4">
<div style="max-width:600px;margin:30px auto;background:#fff;border-radius:12px;overflow:hidden">
<div style="background:linear-gradient(135deg,#4F46E5,#7C3AED);color:#fff;padding:30px;text-align:center"><h1>CampusConnect</h1></div>
<div style="padding:40px;text-align:center"><h2>New OTP</h2>
<div style="background:#EEF2FF;border:2px dashed #4F46E5;border-radius:12px;padding:25px;margin:20px auto;display:inline-block">
<p style="font-size:44px;font-weight:900;color:#4F46E5;letter-spacing:12px;margin:0;font-family:monospace">{otp}</p></div>
<p style="color:#EF4444;font-weight:bold">Expires in 10 minutes</p></div></div></body>"""
            send_async(p['email'], f'CampusConnect New OTP: {otp}', html)
            flash('New OTP sent!', 'success')
            return render_template('reset_password.html', email=p['email'])
        # Validate OTP
        entered = request.form.get('otp', '').strip()
        new_pw  = request.form.get('password', '')
        conf_pw = request.form.get('confirm_password', '')
        if datetime.now() > datetime.strptime(p['otp_expiry'], '%Y-%m-%d %H:%M:%S'):
            flash('OTP expired! Please request a new one.', 'error')
            return render_template('reset_password.html', email=p['email'])
        if entered != p['otp']:
            flash('Invalid OTP!', 'error')
            return render_template('reset_password.html', email=p['email'])
        if len(new_pw) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('reset_password.html', email=p['email'])
        if new_pw != conf_pw:
            flash('Passwords do not match!', 'error')
            return render_template('reset_password.html', email=p['email'])
        db = get_db()
        db.users.update_one({'email': p['email']}, {'$set': {'password': hash_password(new_pw)}})
        session.pop('pending_reset', None)
        flash('Password reset successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', email=p['email'])



@auth_bp.route('/dashboard')
def dashboard():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    from helpers import get_unread_count
    from database import get_users_batch

    def fmt_ride(r, u):
        return (str(r['_id']), r['from_location'], r['to_location'], r.get('ride_date'),
                r.get('ride_time'), r.get('seats_available',0), r.get('price_per_seat',0),
                u['full_name'] if u else 'Unknown')

    def fmt_hostel(h, u):
        imgs = h.get('image_urls') or ([h['image_url']] if h.get('image_url') else [])
        return (str(h['_id']), h['name'], h['location'], h['price'], h.get('gender',''),
                h.get('facilities',''), h.get('contact',''), u['full_name'] if u else 'Unknown', imgs[0] if imgs else None)

    def fmt_item(i, u):
        return (str(i['_id']), i['title'], i['price'], i.get('category',''), i.get('condition',''),
                u['full_name'] if u else 'Unknown')

    # Fetch recent active rides, filter departed ones in Python, and take the first 3
    ride_docs_all = list(db.rides.find({'status':'active'}).sort('created_at',-1).limit(30))
    ride_docs = []
    now_local = datetime.utcnow() + timedelta(hours=5)
    for r in ride_docs_all:
        if r.get('ride_date') and r.get('ride_time'):
            try:
                h, m = map(int, r.get('ride_time', '00:00').split(':'))
                scheduled_dt = r['ride_date'] + timedelta(hours=h, minutes=m)
                if scheduled_dt + timedelta(hours=1) < now_local:
                    continue
            except:
                pass
        ride_docs.append(r)
        if len(ride_docs) == 3:
            break

    hostel_docs  = list(db.hostels.find().sort('created_at',-1).limit(3))
    item_docs    = list(db.marketplace.find({'status':'available'}).sort('created_at',-1).limit(4))

    # Batch-fetch all users in ONE query instead of N+1 individual queries
    all_uids = [r['user_id'] for r in ride_docs] + [h['user_id'] for h in hostel_docs] + [i['user_id'] for i in item_docs]
    users_map = get_users_batch(db, all_uids)

    rides   = [fmt_ride(r, users_map.get(r['user_id']))   for r in ride_docs]
    hostels = [fmt_hostel(h, users_map.get(h['user_id'])) for h in hostel_docs]
    items   = [fmt_item(i, users_map.get(i['user_id']))   for i in item_docs]

    return render_template('dashboard.html',
        rides=rides, hostels=hostels, items=items,
        unread=get_unread_count(),
        total_rides   = db.rides.count_documents({'status':'active'}),
        total_hostels = db.hostels.estimated_document_count(),
        total_items   = db.marketplace.count_documents({'status':'available'}),
        total_users   = db.users.estimated_document_count()
    )


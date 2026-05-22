"""helpers.py — shared utilities across all blueprints."""
import os, time, hashlib, boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
from flask import session
from database import get_db

ALLOWED_IMG  = {'png','jpg','jpeg','gif','webp'}
ALLOWED_PDF  = {'pdf'}

R2_ACCOUNT_ID      = os.environ.get('R2_ACCOUNT_ID','')
R2_ACCESS_KEY_ID   = os.environ.get('R2_ACCESS_KEY_ID','')
R2_SECRET_KEY      = os.environ.get('R2_SECRET_ACCESS_KEY','')
R2_BUCKET          = os.environ.get('R2_BUCKET_NAME','campusconnect')
R2_PUBLIC_URL      = os.environ.get('R2_PUBLIC_URL','')

def _r2():
    if not R2_ACCOUNT_ID:
        return None
    return boto3.client(
        's3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )

def upload_file(file, folder, allowed_exts):
    if not file or not file.filename:
        return None
    ext = file.filename.rsplit('.',1)[-1].lower()
    if ext not in allowed_exts:
        return None
    fname  = f"{folder}/{int(time.time())}_{secure_filename(file.filename)}"
    ctype  = 'application/pdf' if ext=='pdf' else f'image/{ext}'
    r2 = _r2()
    if r2:
        try:
            r2.upload_fileobj(file, R2_BUCKET, fname, ExtraArgs={'ContentType': ctype})
            return f"{R2_PUBLIC_URL}/{fname}" if R2_PUBLIC_URL else fname
        except Exception as e:
            print(f"R2 upload error: {e}")
    # local fallback
    local = os.path.join('static','uploads', fname)
    os.makedirs(os.path.dirname(local), exist_ok=True)
    file.seek(0)
    file.save(local)
    return f"/static/uploads/{fname}"

def upload_files(files, folder, allowed_exts, max_files=5):
    """Upload multiple files (up to max_files). Returns a list of URLs."""
    urls = []
    for f in files[:max_files]:
        url = upload_file(f, folder, allowed_exts)
        if url:
            urls.append(url)
    return urls

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def is_logged_in():
    return 'user_id' in session

def get_unread_count():
    if not is_logged_in():
        return 0
    try:
        db = get_db()
        return db.messages.count_documents({'receiver_id': session['user_id'], 'is_read': False})
    except:
        return 0

def is_valid_email(email):
    domains = ['@comsats.edu.pk','@student.comsats.edu.pk','@ciit.edu.pk',
               '@isbstudent.comsats.edu.pk','@isb.student.comsats.edu.pk',
               '@lhr.student.comsats.edu.pk','@khi.student.comsats.edu.pk',
               '@wah.student.comsats.edu.pk','@gmail.com']
    email = email.lower().strip()
    return any(email.endswith(d) for d in domains)

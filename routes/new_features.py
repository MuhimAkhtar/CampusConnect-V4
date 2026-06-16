from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_db
from helpers import is_logged_in, get_unread_count, upload_file, ALLOWED_PDF
from datetime import datetime
from bson import ObjectId
import requests as http_req

new_bp = Blueprint('new_features', __name__)

def get_user(db, uid):
    try: return db.users.find_one({'_id': ObjectId(uid)})
    except: return None

# ─── Past Papers ─────────────────────────────────────────────────────────────

@new_bp.route('/past-papers')
def past_papers():
    db = get_db()
    from database import get_users_batch
    subject     = request.args.get('subject','')
    course_code = request.args.get('course_code','')
    exam_type   = request.args.get('exam_type','')
    exam_year   = request.args.get('exam_year','')
    page        = request.args.get('page', 1, type=int)
    per_page    = 30

    q = {}
    if subject:     q['subject']     = {'$regex': subject, '$options': 'i'}
    if course_code: q['course_code'] = {'$regex': course_code, '$options': 'i'}
    if exam_type:   q['exam_type']   = exam_type
    if exam_year:
        try: q['exam_year'] = int(exam_year)
        except: pass

    if not q:
        total = db.past_papers.estimated_document_count()
    else:
        total = db.past_papers.count_documents(q)
        
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    skip = (page - 1) * per_page

    docs = list(db.past_papers.find(q).sort('created_at', -1).skip(skip).limit(per_page))

    # Batch-fetch all uploaders in ONE query instead of N+1
    user_ids = [p['user_id'] for p in docs]
    users_map = get_users_batch(db, user_ids)

    papers = []
    for p in docs:
        u = users_map.get(p['user_id'])
        papers.append({
            'id':          str(p['_id']),
            'subject':     p.get('subject',''),
            'course_code': p.get('course_code',''),
            'exam_year':   p.get('exam_year',''),
            'exam_type':   p.get('exam_type',''),
            'semester':    p.get('semester',''),
            'file_url':    p.get('file_url',''),
            'uploaded_by': u['full_name'] if u else 'Unknown',
            'created_at':  p.get('created_at'),
        })

    from flask import make_response
    resp = make_response(render_template('past_papers.html', papers=papers,
                           subject=subject, course_code=course_code,
                           exam_type=exam_type, exam_year=exam_year,
                           page=page, total_pages=total_pages, total=total,
                           unread=get_unread_count()))
    
    # Securely vary cache by session cookie to prevent logged-in users from seeing cached templates
    resp.headers['Vary'] = 'Cookie'
    
    if not is_logged_in():
        # Cache publicly at Vercel CDN for 60 seconds, stale-while-revalidate for 10 minutes
        resp.headers['Cache-Control'] = 'public, max-age=10, s-maxage=60, stale-while-revalidate=600'
    else:
        # Logged-in users should never hit cache
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        
    return resp

@new_bp.route('/past-papers/upload', methods=['GET','POST'])
def upload_paper():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    if request.method == 'POST':
        file_url = upload_file(request.files.get('pdf'), 'papers', ALLOWED_PDF)
        if not file_url:
            flash('Please upload a valid PDF file!','error')
            return render_template('upload_paper.html', unread=get_unread_count())
        db = get_db()
        try: year = int(request.form.get('exam_year', datetime.utcnow().year))
        except: year = datetime.utcnow().year
        db.past_papers.insert_one({
            'user_id':     session['user_id'],
            'subject':     request.form.get('subject','').strip(),
            'course_code': request.form.get('course_code','').strip().upper(),
            'exam_year':   year,
            'exam_type':   request.form.get('exam_type','Mid'),
            'semester':    request.form.get('semester','').strip(),
            'file_url':    file_url,
            'created_at':  datetime.utcnow()
        })
        flash('Past paper uploaded successfully!','success')
        return redirect(url_for('new_features.past_papers'))
    return render_template('upload_paper.html', unread=get_unread_count())

# ─── LMS Portal ──────────────────────────────────────────────────────────────

@new_bp.route('/lms')
def lms_portal():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    return render_template('lms_portal.html', unread=get_unread_count())

@new_bp.route('/lms/status')
def lms_status():
    """Server-side reachability check for SIS — avoids browser CORS issues."""
    try:
        r = http_req.get('https://sis.comsats.edu.pk', timeout=6, allow_redirects=True)
        online = r.status_code < 500
    except Exception:
        online = False
    return jsonify({'online': online})

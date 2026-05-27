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
    subject     = request.args.get('subject','')
    course_code = request.args.get('course_code','')
    exam_type   = request.args.get('exam_type','')
    exam_year   = request.args.get('exam_year','')
    q = {}
    if subject:     q['subject']     = {'$regex': subject, '$options': 'i'}
    if course_code: q['course_code'] = {'$regex': course_code, '$options': 'i'}
    if exam_type:   q['exam_type']   = exam_type
    if exam_year:
        try: q['exam_year'] = int(exam_year)
        except: pass
    docs = list(db.past_papers.find(q).sort('created_at',-1))
    papers = []
    for p in docs:
        u = get_user(db, p['user_id'])
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
    return render_template('past_papers.html', papers=papers,
        subject=subject, course_code=course_code,
        exam_type=exam_type, exam_year=exam_year,
        unread=get_unread_count())

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

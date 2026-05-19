from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from helpers import is_logged_in, get_unread_count, upload_file, ALLOWED_IMG
from datetime import datetime
from bson import ObjectId

hostels_bp = Blueprint('hostels', __name__)

def get_user(db, uid):
    try: return db.users.find_one({'_id': ObjectId(uid)})
    except: return None

def fmt(h, u):
    return (str(h['_id']), h['name'], h['location'], h['price'],
            h.get('gender',''), h.get('facilities',''), h.get('contact',''),
            u['full_name'] if u else 'Unknown',
            h.get('image_url'))

@hostels_bp.route('/hostels')
def hostels():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    search = request.args.get('search','')
    gender = request.args.get('gender','')
    db = get_db()
    q = {}
    if search:
        q['$or'] = [{'name':{'$regex':search,'$options':'i'}},
                    {'location':{'$regex':search,'$options':'i'}}]
    if gender: q['gender'] = gender
    docs = list(db.hostels.find(q).sort('created_at',-1))
    result = [fmt(h, get_user(db, h['user_id'])) for h in docs]
    return render_template('hostels.html', hostels=result, search=search, gender=gender, unread=get_unread_count())

@hostels_bp.route('/hostels/post', methods=['GET','POST'])
def post_hostel():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    if request.method == 'POST':
        image_url = upload_file(request.files.get('image'), 'hostels', ALLOWED_IMG)
        db = get_db()
        db.hostels.insert_one({
            'user_id': session['user_id'],
            'name': request.form['name'], 'location': request.form['location'],
            'price': float(request.form['price']), 'gender': request.form['gender'],
            'facilities': request.form['facilities'], 'contact': request.form['contact'],
            'image_url': image_url, 'created_at': datetime.utcnow()
        })
        flash('Hostel listed!','success')
        return redirect(url_for('hostels.hostels'))
    return render_template('post_hostel.html', unread=get_unread_count())

@hostels_bp.route('/hostels/<hostel_id>')
def hostel_detail(hostel_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    try: h = db.hostels.find_one({'_id': ObjectId(hostel_id)})
    except: return redirect(url_for('hostels.hostels'))
    if not h: return redirect(url_for('hostels.hostels'))
    u = get_user(db, h['user_id'])
    hostel = (str(h['_id']), h['name'], h['location'], h['price'],
              h.get('gender',''), h.get('facilities',''), h.get('contact',''),
              u['full_name'] if u else '?', u['email'] if u else '', str(u['_id']) if u else None,
              h.get('image_url'))
    bookmarked = db.hostel_bookmarks.count_documents({'user_id':session['user_id'],'hostel_id':hostel_id}) > 0
    rev_docs = list(db.reviews.find({'target_type':'HOSTEL','target_id':hostel_id}).sort('created_at',-1))
    reviews = []
    for rv in rev_docs:
        ru = get_user(db, rv['reviewer_id'])
        reviews.append((ru['full_name'] if ru else '?', rv.get('rating'), rv.get('comments','')))
    return render_template('hostel_detail.html', hostel=hostel, is_bookmarked=bookmarked,
                           reviews=reviews, unread=get_unread_count())

@hostels_bp.route('/hostels/bookmark/<hostel_id>')
def bookmark_hostel(hostel_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    existing = db.hostel_bookmarks.find_one({'user_id':session['user_id'],'hostel_id':hostel_id})
    if existing:
        db.hostel_bookmarks.delete_one({'_id':existing['_id']})
        flash('Bookmark removed!','success')
    else:
        db.hostel_bookmarks.insert_one({'user_id':session['user_id'],'hostel_id':hostel_id,'created_at':datetime.utcnow()})
        flash('Hostel bookmarked!','success')
    return redirect(url_for('hostels.hostel_detail', hostel_id=hostel_id))

@hostels_bp.route('/hostels/delete/<hostel_id>')
def delete_hostel(hostel_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    db.hostels.delete_one({'_id':ObjectId(hostel_id),'user_id':session['user_id']})
    flash('Hostel removed!','success')
    return redirect(url_for('misc.profile'))

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from helpers import is_logged_in, get_unread_count, upload_file, ALLOWED_IMG
from datetime import datetime
from bson import ObjectId

misc_bp = Blueprint('misc', __name__)

def get_user(db, uid):
    try: return db.users.find_one({'_id': ObjectId(uid)})
    except: return None

@misc_bp.route('/notifications')
def notifications():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    uid = session['user_id']
    notifs_docs = list(db.notifications.find({'user_id':uid}).sort('created_at',-1))
    db.notifications.update_many({'user_id':uid,'is_read':False},{'$set':{'is_read':True}})
    notifs = [(str(n['_id']), n['title'], n['message'], n.get('notif_type','general'),
               n.get('is_read',False), n.get('created_at')) for n in notifs_docs]
    return render_template('notifications.html', notifs=notifs, unread=0)

@misc_bp.route('/search')
def global_search():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    kw = request.args.get('q', '').strip()
    results = {'rides': [], 'hostels': [], 'items': []}
    if kw:
        try:
            db = get_db()
            pat = {'$regex': kw, '$options': 'i'}

            # ── Rides ──────────────────────────────────────────────────────────
            rides_docs = list(db.rides.find(
                {'status': 'active', '$or': [{'from_location': pat}, {'to_location': pat}]}
            ))
            for r in rides_docs:
                try:
                    u = get_user(db, r.get('user_id', ''))
                    results['rides'].append((
                        str(r['_id']),
                        r.get('from_location', ''),
                        r.get('to_location', ''),
                        r.get('ride_date'),               # can be None — template handles it
                        r.get('ride_time', ''),
                        r.get('seats_available', 0),
                        r.get('price_per_seat', 0),
                        u['full_name'] if u else '?'
                    ))
                except Exception:
                    continue

            # ── Hostels ────────────────────────────────────────────────────────
            hostels_docs = list(db.hostels.find(
                {'$or': [{'name': pat}, {'location': pat}]}
            ))
            for h in hostels_docs:
                try:
                    results['hostels'].append((
                        str(h['_id']),
                        h.get('name', ''),
                        h.get('location', ''),
                        h.get('price', 0),
                        h.get('gender', ''),
                        h.get('facilities', '')
                    ))
                except Exception:
                    continue

            # ── Marketplace ────────────────────────────────────────────────────
            items_docs = list(db.marketplace.find(
                {'status': 'available', '$or': [{'title': pat}, {'description': pat}]}
            ))
            for m in items_docs:
                try:
                    u = get_user(db, m.get('user_id', ''))
                    results['items'].append((
                        str(m['_id']),
                        m.get('title', ''),
                        m.get('price', 0),
                        m.get('category', ''),
                        m.get('condition', ''),
                        u['full_name'] if u else '?'
                    ))
                except Exception:
                    continue

        except Exception as e:
            flash(f'Search error: {e}', 'error')

    return render_template('search_results.html', results=results,
                           keyword=kw, unread=get_unread_count())

@misc_bp.route('/profile')
def profile():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    uid = session['user_id']
    user_doc = get_user(db, uid)
    if not user_doc: return redirect(url_for('auth.login'))
    user = (uid, user_doc['full_name'], user_doc['email'],
            user_doc.get('university',''), user_doc.get('created_at'))
    profile_pic = user_doc.get('profile_pic', '')
    rides_docs = list(db.rides.find({'user_id':uid}).sort('created_at',-1))
    my_rides = [(str(r['_id']), r['from_location'], r['to_location'], r.get('ride_date'), r.get('status','')) for r in rides_docs]
    items_docs = list(db.marketplace.find({'user_id':uid}).sort('created_at',-1))
    my_items = [(str(m['_id']), m['title'], m['price'], m.get('category',''), m.get('status','')) for m in items_docs]
    hostels_docs = list(db.hostels.find({'user_id':uid}).sort('created_at',-1))
    my_hostels = [(str(h['_id']), h['name'], h['location'], h['price']) for h in hostels_docs]
    prof_doc = db.user_profiles.find_one({'user_id':uid})
    user_profile = None
    if prof_doc:
        user_profile = (prof_doc.get('department',''), prof_doc.get('semester',''),
                        prof_doc.get('roll_no',''), prof_doc.get('bio',''),
                        prof_doc.get('phone',''), prof_doc.get('city',''))
    return render_template('profile.html', user=user, my_rides=my_rides, my_items=my_items,
                           my_hostels=my_hostels, user_profile=user_profile,
                           profile_pic=profile_pic, unread=get_unread_count())

@misc_bp.route('/profile/edit', methods=['GET','POST'])
def edit_profile():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    uid = session['user_id']
    if request.method == 'POST':
        # Handle profile picture upload
        pic_url = None
        if 'profile_pic' in request.files:
            pic_file = request.files['profile_pic']
            if pic_file and pic_file.filename:
                pic_url = upload_file(pic_file, 'avatars', ALLOWED_IMG)

        data = {'user_id': uid, 'department': request.form.get('department',''),
                'semester': request.form.get('semester',''), 'roll_no': request.form.get('roll_no',''),
                'bio': request.form.get('bio',''), 'phone': request.form.get('phone',''),
                'city': request.form.get('city',''), 'updated_at': datetime.utcnow()}
        db.user_profiles.update_one({'user_id': uid}, {'$set': data}, upsert=True)

        # Save profile pic to users collection and update session
        if pic_url:
            db.users.update_one({'_id': ObjectId(uid)}, {'$set': {'profile_pic': pic_url}})
            session['profile_pic'] = pic_url
            session.modified = True

        flash('Profile updated!', 'success')
        return redirect(url_for('misc.profile'))

    prof_doc = db.user_profiles.find_one({'user_id': uid})
    prof = None
    if prof_doc:
        prof = (prof_doc.get('department',''), prof_doc.get('semester',''), prof_doc.get('roll_no',''),
                prof_doc.get('bio',''), prof_doc.get('phone',''), prof_doc.get('city',''))

    # Get current profile pic
    user_doc = get_user(db, uid)
    current_pic = user_doc.get('profile_pic', '') if user_doc else ''

    return render_template('edit_profile.html', prof=prof, current_pic=current_pic, unread=get_unread_count())

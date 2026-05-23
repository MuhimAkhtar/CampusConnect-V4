from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from helpers import is_logged_in, get_unread_count, upload_file, ALLOWED_IMG
from datetime import datetime
from bson import ObjectId

events_bp = Blueprint('events', __name__)

def get_user(db, uid):
    try: return db.users.find_one({'_id': ObjectId(uid)})
    except: return None

CATEGORIES = ['Academic', 'Social', 'Sports', 'Career', 'Cultural', 'Other']

def fmt(e, u, db):
    going = db.event_rsvps.count_documents({'event_id': str(e['_id']), 'rsvp_type': 'going'})
    interested = db.event_rsvps.count_documents({'event_id': str(e['_id']), 'rsvp_type': 'interested'})
    return (str(e['_id']),                          # 0  id
            e['title'],                              # 1  title
            e.get('description', ''),                # 2  description
            e.get('event_date', ''),                 # 3  event_date (string YYYY-MM-DD)
            e.get('event_time', ''),                 # 4  event_time (string HH:MM)
            e.get('venue', ''),                      # 5  venue
            e.get('category', ''),                   # 6  category
            e.get('image_url'),                      # 7  image_url
            u['full_name'] if u else 'Unknown',      # 8  poster name
            u.get('profile_pic', '') if u else '',   # 9  poster pic
            str(u['_id']) if u else None,             # 10 poster id
            going,                                   # 11 going count
            interested,                              # 12 interested count
            e.get('registration_link', ''),          # 13 registration_link
            e.get('created_at'))                      # 14 created_at


@events_bp.route('/events')
def events():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    search   = request.args.get('search', '')
    category = request.args.get('category', '')
    db = get_db()
    q = {}
    if search:
        q['$or'] = [{'title': {'$regex': search, '$options': 'i'}},
                     {'description': {'$regex': search, '$options': 'i'}}]
    if category: q['category'] = category
    docs = list(db.events.find(q).sort('event_date', 1))
    items = [fmt(e, get_user(db, e['user_id']), db) for e in docs]
    return render_template('events.html', events=items, search=search,
                           category=category, categories=CATEGORIES,
                           unread=get_unread_count())


@events_bp.route('/events/post', methods=['GET', 'POST'])
def post_event():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    if request.method == 'POST':
        image_url = upload_file(request.files.get('image'), 'events', ALLOWED_IMG)
        db = get_db()
        db.events.insert_one({
            'user_id': session['user_id'],
            'title': request.form['title'],
            'description': request.form['description'],
            'event_date': request.form['event_date'],
            'event_time': request.form.get('event_time', ''),
            'venue': request.form['venue'],
            'category': request.form['category'],
            'image_url': image_url,
            'registration_link': request.form.get('registration_link', '').strip(),
            'created_at': datetime.utcnow()
        })
        flash('Event posted successfully!', 'success')
        return redirect(url_for('events.events'))
    return render_template('post_event.html', categories=CATEGORIES,
                           unread=get_unread_count())


@events_bp.route('/events/<event_id>')
def event_detail(event_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    try: e = db.events.find_one({'_id': ObjectId(event_id)})
    except: return redirect(url_for('events.events'))
    if not e: return redirect(url_for('events.events'))
    u = get_user(db, e['user_id'])
    item = fmt(e, u, db)
    # Current user's RSVP status
    user_rsvp = db.event_rsvps.find_one({'event_id': event_id, 'user_id': session['user_id']})
    rsvp_status = user_rsvp['rsvp_type'] if user_rsvp else None
    return render_template('event_detail.html', event=item, rsvp_status=rsvp_status,
                           unread=get_unread_count())


@events_bp.route('/events/<event_id>/rsvp', methods=['POST'])
def rsvp_event(event_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    rsvp_type = request.form.get('rsvp_type', '')  # 'going', 'interested', or 'none'
    existing = db.event_rsvps.find_one({'event_id': event_id, 'user_id': session['user_id']})
    if rsvp_type == 'none' or (existing and existing['rsvp_type'] == rsvp_type):
        # Remove RSVP (toggle off)
        if existing:
            db.event_rsvps.delete_one({'_id': existing['_id']})
            flash('RSVP removed!', 'success')
    elif existing:
        # Update RSVP type
        db.event_rsvps.update_one({'_id': existing['_id']}, {'$set': {'rsvp_type': rsvp_type}})
        flash(f'RSVP updated to {rsvp_type.title()}!', 'success')
    else:
        # New RSVP
        db.event_rsvps.insert_one({
            'user_id': session['user_id'],
            'event_id': event_id,
            'rsvp_type': rsvp_type,
            'created_at': datetime.utcnow()
        })
        flash(f"You're {rsvp_type.title()} for this event!", 'success')
    return redirect(url_for('events.event_detail', event_id=event_id))


@events_bp.route('/events/delete/<event_id>')
def delete_event(event_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    db.events.delete_one({'_id': ObjectId(event_id), 'user_id': session['user_id']})
    db.event_rsvps.delete_many({'event_id': event_id})
    flash('Event deleted!', 'success')
    return redirect(url_for('events.events'))

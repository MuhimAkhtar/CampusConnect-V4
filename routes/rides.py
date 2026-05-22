from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from helpers import is_logged_in, get_unread_count, upload_file, ALLOWED_IMG
from datetime import datetime
from bson import ObjectId

rides_bp = Blueprint('rides', __name__)

def get_user(db, uid):
    try: return db.users.find_one({'_id': ObjectId(uid)})
    except: return None

def fmt(r, u, full=False):
    row = (str(r['_id']), r['from_location'], r['to_location'],
           r.get('ride_date'), r.get('ride_time'), r.get('seats_available',0),
           r.get('price_per_seat',0), u['full_name'] if u else 'Unknown',
           str(u['_id']) if u else None,
           r.get('pickup_lat'), r.get('pickup_lng'), r.get('dropoff_lat'), r.get('dropoff_lng'),
           r.get('distance_km'), r.get('duration_mins'), r.get('status','active'),
           u['email'] if u else '', u.get('profile_pic','') if u else '')
    return row

@rides_bp.route('/rides')
def rides():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    search = request.args.get('search','')
    db = get_db()
    q = {'status':'active'}
    if search:
        q['$or'] = [{'from_location':{'$regex':search,'$options':'i'}},
                    {'to_location':{'$regex':search,'$options':'i'}}]
    docs = list(db.rides.find(q).sort('ride_date', 1))
    result = [fmt(r, get_user(db, r['user_id'])) for r in docs]
    return render_template('rides.html', rides=result, search=search, unread=get_unread_count())

@rides_bp.route('/rides/post', methods=['GET','POST'])
def post_ride():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    if request.method == 'POST':
        f = request.form
        db = get_db()
        ride_date = None
        try: ride_date = datetime.strptime(f['ride_date'],'%Y-%m-%d')
        except: pass
        db.rides.insert_one({
            'user_id': session['user_id'],
            'from_location': f['from_location'], 'to_location': f['to_location'],
            'ride_date': ride_date, 'ride_time': f['ride_time'],
            'seats_available': int(f.get('seats',1)), 'price_per_seat': float(f.get('price',0)),
            'status': 'active',
            'pickup_lat':  float(f['pickup_lat'])  if f.get('pickup_lat')  else None,
            'pickup_lng':  float(f['pickup_lng'])  if f.get('pickup_lng')  else None,
            'dropoff_lat': float(f['dropoff_lat']) if f.get('dropoff_lat') else None,
            'dropoff_lng': float(f['dropoff_lng']) if f.get('dropoff_lng') else None,
            'distance_km':  float(f['distance_km'])   if f.get('distance_km')   else None,
            'duration_mins': int(f['duration_mins'])  if f.get('duration_mins') else None,
            'created_at': datetime.utcnow()
        })
        flash('Ride posted!','success')
        return redirect(url_for('rides.rides'))
    return render_template('post_ride.html', unread=get_unread_count())

@rides_bp.route('/rides/<ride_id>')
def ride_detail(ride_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    try: r = db.rides.find_one({'_id': ObjectId(ride_id)})
    except: return redirect(url_for('rides.rides'))
    if not r: return redirect(url_for('rides.rides'))
    u = get_user(db, r['user_id'])
    ride = fmt(r, u, full=True)
    reqs_docs = list(db.ride_requests.find({'ride_id': ride_id}))
    reqs = []
    for rq in reqs_docs:
        ru = get_user(db, rq['user_id'])
        reqs.append((ru['full_name'] if ru else '?', rq.get('status','pending'), rq.get('created_at'), rq['user_id']))
    already = db.ride_requests.count_documents({'ride_id': ride_id, 'user_id': session['user_id']}) > 0
    rev_docs = list(db.reviews.find({'target_type':'RIDE','target_id':ride_id}).sort('created_at',-1))
    reviews = []
    for rv in rev_docs:
        ru = get_user(db, rv['reviewer_id'])
        reviews.append((ru['full_name'] if ru else '?', rv.get('rating'), rv.get('comments','')))
    return render_template('ride_detail.html', ride=ride, requests=reqs,
                           already_requested=already, reviews=reviews, unread=get_unread_count())

@rides_bp.route('/rides/request/<ride_id>')
def request_ride(ride_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    db.ride_requests.insert_one({'ride_id':ride_id,'user_id':session['user_id'],'status':'pending','created_at':datetime.utcnow()})
    r = db.rides.find_one({'_id': ObjectId(ride_id)})
    if r:
        requester = get_user(db, session['user_id'])
        requester_name = requester['full_name'] if requester else 'A user'
        db.notifications.insert_one({'user_id':r['user_id'],'title':'New Ride Request!',
            'message':f"{requester_name} requested a seat on your ride.",
            'notif_type':'ride_request','is_read':False,'created_at':datetime.utcnow()})
    flash('Ride request sent!','success')
    return redirect(url_for('rides.ride_detail', ride_id=ride_id))

@rides_bp.route('/rides/accept/<ride_id>/<user_id>')
def accept_ride(ride_id, user_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    db.ride_requests.update_one({'ride_id':ride_id,'user_id':user_id},{'$set':{'status':'approved'}})
    db.ride_passengers.insert_one({'ride_id':ride_id,'user_id':user_id,'status':'confirmed','joined_at':datetime.utcnow()})
    db.rides.update_one({'_id':ObjectId(ride_id)},{'$inc':{'seats_available':-1}})
    db.notifications.insert_one({'user_id':user_id,'title':'Ride Request Accepted!',
        'message':'Your ride request was accepted!','notif_type':'ride_request','is_read':False,'created_at':datetime.utcnow()})
    flash('Request accepted!','success')
    return redirect(url_for('rides.ride_detail', ride_id=ride_id))

@rides_bp.route('/rides/reject/<ride_id>/<user_id>')
def reject_ride(ride_id, user_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    db.ride_requests.update_one({'ride_id':ride_id,'user_id':user_id},{'$set':{'status':'rejected'}})
    db.notifications.insert_one({'user_id':user_id,'title':'Ride Request Rejected',
        'message':'Your ride request was not accepted.','notif_type':'ride_request','is_read':False,'created_at':datetime.utcnow()})
    flash('Request rejected.','success')
    return redirect(url_for('rides.ride_detail', ride_id=ride_id))

@rides_bp.route('/rides/delete/<ride_id>')
def delete_ride(ride_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    db.rides.update_one({'_id':ObjectId(ride_id),'user_id':session['user_id']},{'$set':{'status':'cancelled'}})
    flash('Ride cancelled!','success')
    return redirect(url_for('misc.profile'))

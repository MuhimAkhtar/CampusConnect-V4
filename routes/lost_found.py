from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from helpers import is_logged_in, get_unread_count, upload_file, ALLOWED_IMG
from datetime import datetime
from bson import ObjectId

lost_found_bp = Blueprint('lost_found', __name__)

def get_user(db, uid):
    try: return db.users.find_one({'_id': ObjectId(uid)})
    except: return None

def fmt(item, u):
    created = item.get('created_at', datetime.utcnow())
    date_str = created.strftime('%b %d, %Y') if created else ''
    return (str(item['_id']), item['title'], item.get('description',''),
            item['type'], item.get('location',''), date_str,
            item.get('image_url'), u['full_name'] if u else 'Unknown',
            str(u['_id']) if u else None, u.get('profile_pic','') if u else '',
            item.get('status','active'), created)

@lost_found_bp.route('/lost-found')
def lost_found():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    search = request.args.get('search','')
    item_type = request.args.get('type','')
    db = get_db()
    q = {}
    if search:
        q['$or'] = [{'title':{'$regex':search,'$options':'i'}},
                    {'description':{'$regex':search,'$options':'i'}},
                    {'location':{'$regex':search,'$options':'i'}}]
    if item_type: q['type'] = item_type
    docs = list(db.lost_found.find(q).sort('created_at',-1))
    items = [fmt(d, get_user(db, d['user_id'])) for d in docs]
    return render_template('lost_found.html', items=items, search=search,
                           item_type=item_type, unread=get_unread_count())

@lost_found_bp.route('/lost-found/post', methods=['GET','POST'])
def post_lost_found():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    if request.method == 'POST':
        image_url = upload_file(request.files.get('image'), 'lost_found', ALLOWED_IMG)
        db = get_db()
        db.lost_found.insert_one({
            'user_id': session['user_id'],
            'title': request.form['title'],
            'description': request.form['description'],
            'type': request.form['type'],
            'location': request.form['location'],
            'image_url': image_url,
            'status': 'active',
            'created_at': datetime.utcnow()
        })
        flash('Item posted successfully!','success')
        return redirect(url_for('lost_found.lost_found'))
    return render_template('post_lost_found.html', unread=get_unread_count())

@lost_found_bp.route('/lost-found/<item_id>')
def lost_found_detail(item_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    try: d = db.lost_found.find_one({'_id': ObjectId(item_id)})
    except: return redirect(url_for('lost_found.lost_found'))
    if not d: return redirect(url_for('lost_found.lost_found'))
    u = get_user(db, d['user_id'])
    created = d.get('created_at', datetime.utcnow())
    date_str = created.strftime('%b %d, %Y at %I:%M %p') if created else ''
    item = (str(d['_id']), d['title'], d.get('description',''),
            d['type'], d.get('location',''), date_str,
            d.get('image_url'), u['full_name'] if u else 'Unknown',
            u['email'] if u else '', str(u['_id']) if u else None,
            d.get('status','active'), u.get('profile_pic','') if u else '')
    return render_template('lost_found_detail.html', item=item, unread=get_unread_count())

@lost_found_bp.route('/lost-found/resolve/<item_id>')
def resolve_item(item_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    db.lost_found.update_one(
        {'_id': ObjectId(item_id), 'user_id': session['user_id']},
        {'$set': {'status': 'resolved'}}
    )
    flash('Item marked as resolved!','success')
    return redirect(url_for('lost_found.lost_found_detail', item_id=item_id))

@lost_found_bp.route('/lost-found/delete/<item_id>')
def delete_lost_found(item_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    db.lost_found.delete_one({'_id': ObjectId(item_id), 'user_id': session['user_id']})
    flash('Item removed!','success')
    return redirect(url_for('lost_found.lost_found'))

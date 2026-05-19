from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_db
from helpers import is_logged_in, get_unread_count
from datetime import datetime
from bson import ObjectId

messages_bp = Blueprint('messages', __name__)

def get_user(db, uid):
    try: return db.users.find_one({'_id': ObjectId(uid)})
    except: return None

@messages_bp.route('/messages')
def messages():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db  = get_db()
    uid = session['user_id']

    # All user IDs we've talked to
    sent_to  = db.messages.distinct('receiver_id', {'sender_id': uid})
    recv_from = db.messages.distinct('sender_id', {'receiver_id': uid})
    other_ids = list(set(sent_to + recv_from))
    other_ids = [o for o in other_ids if o != uid]

    conversations = []
    for oid in other_ids:
        u = get_user(db, oid)
        name = u['full_name'] if u else 'Unknown User'
        last_msg = db.messages.find_one(
            {'$or':[{'sender_id':uid,'receiver_id':oid},{'sender_id':oid,'receiver_id':uid}]},
            sort=[('created_at',-1)]
        )
        last_time = last_msg['created_at'] if last_msg else None
        unread_from = db.messages.count_documents({'sender_id':oid,'receiver_id':uid,'is_read':False})
        conversations.append((oid, name, last_time, unread_from,
                              last_msg['message'][:40] if last_msg else ''))
    conversations.sort(key=lambda x: x[2] if x[2] else datetime.min, reverse=True)
    return render_template('messages.html', conversations=conversations, unread=get_unread_count())

@messages_bp.route('/messages/<other_id>', methods=['GET','POST'])
def chat(other_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db  = get_db()
    uid = session['user_id']

    if request.method == 'POST':
        msg = request.form.get('message','').strip()
        if msg:
            sender = get_user(db, uid)
            sender_name = sender['full_name'] if sender else 'A user'
            db.messages.insert_one({'sender_id':uid,'receiver_id':other_id,'message':msg,
                'is_read':False,'created_at':datetime.utcnow()})
            db.notifications.insert_one({'user_id':other_id,'title':'New Message!',
                'message':f"New message from {sender_name}",
                'notif_type':'message','is_read':False,'created_at':datetime.utcnow()})
            return redirect(url_for('messages.chat', other_id=other_id))

    # Mark incoming as read
    db.messages.update_many({'sender_id':other_id,'receiver_id':uid,'is_read':False},{'$set':{'is_read':True}})

    chat_docs = list(db.messages.find(
        {'$or':[{'sender_id':uid,'receiver_id':other_id},{'sender_id':other_id,'receiver_id':uid}]}
    ).sort('created_at',1))

    chats = [(c['message'], c['sender_id'], c.get('created_at'), str(c['_id'])) for c in chat_docs]
    other_user_doc = get_user(db, other_id)
    other_user = (other_user_doc['full_name'], other_user_doc['email']) if other_user_doc else ('Unknown','')
    return render_template('chat.html', chats=chats, other_user=other_user,
                           other_id=other_id, unread=get_unread_count())

@messages_bp.route('/messages/<other_id>/poll')
def chat_poll(other_id):
    """AJAX endpoint — returns new messages as JSON since a given timestamp."""
    if not is_logged_in(): return jsonify({'error':'unauthorized'}), 401
    db  = get_db()
    uid = session['user_id']
    since_str = request.args.get('since','')
    since = None
    if since_str:
        try: since = datetime.fromisoformat(since_str)
        except: pass

    # Mark incoming read
    db.messages.update_many({'sender_id':other_id,'receiver_id':uid,'is_read':False},{'$set':{'is_read':True}})

    q = {'$or':[{'sender_id':uid,'receiver_id':other_id},{'sender_id':other_id,'receiver_id':uid}]}
    if since: q['created_at'] = {'$gt': since}
    docs = list(db.messages.find(q).sort('created_at',1))

    result = []
    for d in docs:
        result.append({'message': d['message'], 'sender_id': d['sender_id'],
            'created_at': d['created_at'].isoformat() if d.get('created_at') else None,
            'is_mine': d['sender_id'] == uid,
            '_id': str(d['_id'])})
    return jsonify({'messages': result, 'unread': get_unread_count()})

@messages_bp.route('/messages/send/<other_id>', methods=['POST'])
def send_message(other_id):
    """AJAX send — returns JSON."""
    if not is_logged_in(): return jsonify({'error':'unauthorized'}), 401
    db  = get_db()
    uid = session['user_id']
    msg = request.json.get('message','').strip() if request.is_json else request.form.get('message','').strip()
    if not msg: return jsonify({'error':'empty'}), 400
    sender = get_user(db, uid)
    sender_name = sender['full_name'] if sender else 'A user'
    saved = db.messages.insert_one({'sender_id':uid,'receiver_id':other_id,'message':msg,
        'is_read':False,'created_at':datetime.utcnow()})
    db.notifications.insert_one({'user_id':other_id,'title':'New Message!',
        'message':f"New message from {sender_name}",
        'notif_type':'message','is_read':False,'created_at':datetime.utcnow()})
    return jsonify({'ok':True, '_id': str(saved.inserted_id)})

@messages_bp.route('/users/search')
def user_search():
    """Search users to start a new conversation."""
    if not is_logged_in(): return jsonify([])
    q = request.args.get('q','').strip()
    if len(q) < 2: return jsonify([])
    db = get_db()
    docs = list(db.users.find({'$or':[{'full_name':{'$regex':q,'$options':'i'}},
                                       {'email':{'$regex':q,'$options':'i'}}]}).limit(10))
    return jsonify([{'id':str(d['_id']),'name':d['full_name'],'email':d['email']} for d in docs if str(d['_id']) != session['user_id']])

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
from helpers import is_logged_in, get_unread_count, upload_file, upload_files, ALLOWED_IMG
from datetime import datetime
from bson import ObjectId

marketplace_bp = Blueprint('marketplace', __name__)

def get_user(db, uid):
    try: return db.users.find_one({'_id': ObjectId(uid)})
    except: return None

def _get_images(doc):
    """Return list of image URLs, with backward compat for old single image_url field."""
    urls = doc.get('image_urls')
    if urls and isinstance(urls, list):
        return urls
    single = doc.get('image_url')
    return [single] if single else []

def fmt(m, u):
    imgs = _get_images(m)
    return (str(m['_id']), m['title'], m.get('description',''), m['price'],
            m.get('category',''), m.get('condition',''),
            u['full_name'] if u else '?', str(u['_id']) if u else None,
            imgs[0] if imgs else None,
            u.get('profile_pic','') if u else '')

@marketplace_bp.route('/marketplace')
def marketplace():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    search   = request.args.get('search','')
    category = request.args.get('category','')
    db = get_db()
    q = {'status':'available'}
    if search:
        q['$or'] = [{'title':{'$regex':search,'$options':'i'}},
                    {'description':{'$regex':search,'$options':'i'}}]
    if category: q['category'] = category
    docs = list(db.marketplace.find(q).sort('created_at',-1))
    items = [fmt(m, get_user(db, m['user_id'])) for m in docs]
    return render_template('marketplace.html', items=items, search=search, category=category, unread=get_unread_count())

@marketplace_bp.route('/marketplace/post', methods=['GET','POST'])
def post_item():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    if request.method == 'POST':
        image_urls = upload_files(request.files.getlist('images'), 'marketplace', ALLOWED_IMG, max_files=5)
        db = get_db()
        db.marketplace.insert_one({
            'user_id': session['user_id'],
            'title': request.form['title'], 'description': request.form['description'],
            'price': float(request.form['price']), 'category': request.form['category'],
            'condition': request.form['condition'], 'status':'available',
            'image_urls': image_urls, 'created_at': datetime.utcnow()
        })
        flash('Item listed!','success')
        return redirect(url_for('marketplace.marketplace'))
    return render_template('post_item.html', unread=get_unread_count())

@marketplace_bp.route('/marketplace/<item_id>')
def item_detail(item_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    try: m = db.marketplace.find_one({'_id': ObjectId(item_id)})
    except: return redirect(url_for('marketplace.marketplace'))
    if not m: return redirect(url_for('marketplace.marketplace'))
    u = get_user(db, m['user_id'])
    imgs = _get_images(m)
    item = (str(m['_id']), m['title'], m.get('description',''), m['price'],
            m.get('category',''), m.get('condition',''), m.get('status','available'),
            u['full_name'] if u else '?', u['email'] if u else '', str(u['_id']) if u else None,
            imgs, u.get('profile_pic','') if u else '')
    return render_template('item_detail.html', item=item, unread=get_unread_count())

@marketplace_bp.route('/marketplace/delete/<item_id>')
def delete_item(item_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    db.marketplace.update_one({'_id':ObjectId(item_id),'user_id':session['user_id']},{'$set':{'status':'sold'}})
    flash('Item marked as sold!','success')
    return redirect(url_for('misc.profile'))

@marketplace_bp.route('/marketplace/report/<item_id>', methods=['POST'])
def report_item(item_id):
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    db.item_reports.insert_one({'reporter_id':session['user_id'],'item_id':item_id,
        'reason':request.form.get('reason','Suspicious listing'),'status':'pending','created_at':datetime.utcnow()})
    count = db.item_reports.count_documents({'item_id':item_id})
    if count >= 3:
        db.marketplace.update_one({'_id':ObjectId(item_id)},{'$set':{'status':'flagged'}})
    flash('Item reported!','success')
    return redirect(url_for('marketplace.item_detail', item_id=item_id))

@marketplace_bp.route('/reviews/add', methods=['POST'])
def add_review():
    if not is_logged_in(): return redirect(url_for('auth.login'))
    db = get_db()
    target_type = request.form['target_type']
    target_id   = request.form['target_id']
    existing = db.reviews.find_one({'reviewer_id':session['user_id'],'target_type':target_type,'target_id':target_id})
    if existing:
        db.reviews.update_one({'_id':existing['_id']},{'$set':{'rating':int(request.form['rating']),'comments':request.form.get('comment','')}})
    else:
        db.reviews.insert_one({'reviewer_id':session['user_id'],'target_type':target_type,'target_id':target_id,
            'rating':int(request.form['rating']),'comments':request.form.get('comment',''),'created_at':datetime.utcnow()})
    flash('Review submitted!','success')
    from flask import request as req
    return redirect(req.referrer or url_for('auth.dashboard'))

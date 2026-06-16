from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
from bson import ObjectId
import os

load_dotenv()

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/campusconnect')

_client = None
_indexes_created = False

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(
            MONGO_URI,
            maxPoolSize=5,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            retryWrites=True,
        )
    return _client

def get_db():
    """Return the campusconnect database."""
    global _indexes_created
    client = get_client()
    db = client.get_database('campusconnect')
    
    # Ensure TTL index only once per cold start, not on every request
    if not _indexes_created:
        try:
            db.signup_attempts.create_index("created_at", expireAfterSeconds=900)
            db.past_papers.create_index([("created_at", -1)])
            db.past_papers.create_index([("subject", 1)])
            db.past_papers.create_index([("course_code", 1)])
        except:
            pass
        _indexes_created = True
        
    return db

def get_users_batch(db, user_ids):
    """Fetch multiple users in a single query. Returns {str(id): user_doc}.
    
    Use this instead of calling get_user() in a loop to avoid N+1 queries.
    Example:
        users_map = get_users_batch(db, [r['user_id'] for r in ride_docs])
        user = users_map.get(ride['user_id'])
    """
    oids = []
    for uid in set(user_ids):
        try:
            oids.append(ObjectId(uid))
        except:
            pass
    if not oids:
        return {}
    docs = db.users.find({'_id': {'$in': oids}})
    return {str(d['_id']): d for d in docs}

if __name__ == '__main__':
    print("Connecting to MongoDB... ⏳")
    db = get_db()
    print(f"Connected! Collections: {db.list_collection_names()} 🚀")
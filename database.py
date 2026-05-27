from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/campusconnect')

_client = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client

def get_db():
    """Return the campusconnect database."""
    client = get_client()
    db = client.get_database('campusconnect')
    
    # Ensure TTL index on signup_attempts created_at field (expires after 15 minutes)
    try:
        db.signup_attempts.create_index("created_at", expireAfterSeconds=900)
    except:
        pass
        
    return db

if __name__ == '__main__':
    print("Connecting to MongoDB... ⏳")
    db = get_db()
    print(f"Connected! Collections: {db.list_collection_names()} 🚀")
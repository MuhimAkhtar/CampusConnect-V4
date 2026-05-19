"""
mongo_schema.py — Initialize CampusConnect MongoDB collections.
Run once after setting up your MongoDB Atlas cluster:
    python mongo_schema.py
"""
from database import get_db
from pymongo import ASCENDING, DESCENDING
from datetime import datetime
import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_schema():
    db = get_db()
    print("Creating indexes...")

    # users
    db.users.create_index([("email", ASCENDING)], unique=True)

    # user_profiles
    db.user_profiles.create_index([("user_id", ASCENDING)], unique=True)

    # rides
    db.rides.create_index([("status", ASCENDING), ("created_at", DESCENDING)])

    # ride_requests
    db.ride_requests.create_index([("ride_id", ASCENDING), ("user_id", ASCENDING)])

    # hostels
    db.hostels.create_index([("created_at", DESCENDING)])

    # hostel_bookmarks
    db.hostel_bookmarks.create_index(
        [("user_id", ASCENDING), ("hostel_id", ASCENDING)], unique=True
    )

    # marketplace
    db.marketplace.create_index([("status", ASCENDING), ("created_at", DESCENDING)])

    # messages
    db.messages.create_index([("sender_id", ASCENDING), ("receiver_id", ASCENDING)])
    db.messages.create_index([("receiver_id", ASCENDING), ("is_read", ASCENDING)])
    db.messages.create_index([("created_at", ASCENDING)])

    # notifications
    db.notifications.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

    # reviews
    db.reviews.create_index(
        [("target_type", ASCENDING), ("target_id", ASCENDING)]
    )

    # past_papers
    db.past_papers.create_index([("course_code", ASCENDING), ("exam_year", DESCENDING)])

    print("✅ Indexes created!")

    # Sample data (skip if already exists)
    if db.users.count_documents({}) == 0:
        print("Inserting sample data...")
        u1 = db.users.insert_one({
            "full_name": "Muhim Akhtar",
            "email": "fa24-bse-080@isbstudent.comsats.edu.pk",
            "password": hash_password("password123"),
            "university": "COMSATS University Islamabad",
            "created_at": datetime.utcnow()
        })
        u2 = db.users.insert_one({
            "full_name": "Izhan Shah",
            "email": "fa24-bse-095@isbstudent.comsats.edu.pk",
            "password": hash_password("password123"),
            "university": "COMSATS University Islamabad",
            "created_at": datetime.utcnow()
        })

        uid1 = str(u1.inserted_id)
        uid2 = str(u2.inserted_id)

        # Profiles
        db.user_profiles.insert_many([
            {
                "user_id": uid1,
                "department": "Software Engineering",
                "semester": "FA24",
                "roll_no": "FA24-BSE-080",
                "bio": "Software Engineering student at COMSATS Islamabad.",
                "phone": "0311-1234567",
                "city": "Rawalpindi",
                "created_at": datetime.utcnow()
            },
            {
                "user_id": uid2,
                "department": "Software Engineering",
                "semester": "FA24",
                "roll_no": "FA24-BSE-095",
                "bio": "Software Engineering student at COMSATS Islamabad.",
                "phone": "0300-9876543",
                "city": "Islamabad",
                "created_at": datetime.utcnow()
            }
        ])

        # Ride
        r1 = db.rides.insert_one({
            "user_id": uid1,
            "from_location": "Rawalpindi Saddar",
            "to_location": "COMSATS University Islamabad",
            "ride_date": datetime(2026, 6, 10),
            "ride_time": "08:00 AM",
            "seats_available": 3,
            "price_per_seat": 150,
            "status": "active",
            "created_at": datetime.utcnow()
        })

        # Hostel
        db.hostels.insert_one({
            "user_id": uid1,
            "name": "Al-Rehman Boys Hostel",
            "location": "Koral Town, Islamabad",
            "price": 8000,
            "gender": "Male",
            "facilities": "WiFi, Laundry, Generator, Water Cooler",
            "contact": "0300-1234567",
            "image_url": None,
            "created_at": datetime.utcnow()
        })

        # Marketplace item
        db.marketplace.insert_one({
            "user_id": uid2,
            "title": "Calculus Textbook 10th Edition",
            "description": "Good condition, no missing pages, minor highlights",
            "price": 500,
            "category": "Books",
            "condition": "Good",
            "status": "available",
            "image_url": None,
            "created_at": datetime.utcnow()
        })

        # Welcome notification
        db.notifications.insert_many([
            {
                "user_id": uid1,
                "title": "Welcome to CampusConnect!",
                "message": "Your account is verified. Start exploring!",
                "notif_type": "general",
                "is_read": False,
                "created_at": datetime.utcnow()
            },
            {
                "user_id": uid2,
                "title": "Welcome to CampusConnect!",
                "message": "Your account is verified. Start exploring!",
                "notif_type": "general",
                "is_read": False,
                "created_at": datetime.utcnow()
            }
        ])

        print("✅ Sample data inserted!")
        print(f"   User 1 email: fa24-bse-080@isbstudent.comsats.edu.pk | password: password123")
        print(f"   User 2 email: fa24-bse-095@isbstudent.comsats.edu.pk | password: password123")
    else:
        print("ℹ️  Database already has data, skipping sample inserts.")

    print("\n🎉 MongoDB schema initialization complete!")


if __name__ == "__main__":
    init_schema()

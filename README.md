# 🎓 CampusConnect V4

CampusConnect is a comprehensive web-based platform designed specifically for university students. It serves as a centralized hub to buy/sell items, find carpools, browse hostel accommodations, share past exam papers, and access official university services—all in one place.

V4 represents a major architectural upgrade, migrating the platform to a highly scalable **MongoDB Atlas** database, integrating **Cloudflare R2** for fast cloud media storage, and implementing a fully custom **Real-Time AJAX Messaging System**.

---

## ✨ Key Features

- **🛍️ Marketplace:** Students can list items (books, electronics, etc.) for sale, browse categories, and message sellers directly.
- **🚗 Ride Sharing:** A carpool system where students can request or offer rides, complete with Accept/Reject driver workflows and interactive Google Maps integration.
- **🏠 Hostel Finder:** Browse local hostels, view facilities, and read student reviews.
- **📚 Past Papers Repository:** A crowdsourced database for uploading and downloading PDF study materials and past exams.
- **💬 Real-Time Chat:** An instant messaging system featuring unread notifications, PKT timezone synchronization, and zero-refresh AJAX polling.
- **🏫 Smart LMS Portal:** Direct, stylized deep-links to official university portals (SIS, Email, Library) bypassing rigid iframe security restrictions.

---

## 🛠️ Technology Stack

- **Backend:** Python, Flask, Jinja2
- **Database:** MongoDB Atlas (PyMongo)
- **Cloud Storage:** Cloudflare R2 (boto3)
- **Frontend:** HTML5, Vanilla JavaScript, Custom CSS Variables
- **Deployment:** Render (Gunicorn)

---

## 🚀 Local Development Setup

To run CampusConnect locally, follow these steps:

### 1. Clone the repository
```bash
git clone https://github.com/MuhimAkhtar/CampusConnect-V4.git
cd CampusConnect-V4
```

### 2. Install Dependencies
Make sure you have Python 3 installed, then run:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a file named `.env` in the root directory and add your secret keys. You can use the provided `.env.example` as a template:

```env
SECRET_KEY=your_super_secret_key
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/campusconnect

# Cloudflare R2
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=campusconnect
R2_PUBLIC_URL=https://your-r2-dev-url.com
```

### 4. Run the Application
Start the Flask development server:
```bash
python app.py
```
Open your browser and navigate to `http://localhost:5000`.

---

## ☁️ Deployment (Render)

This application is configured for seamless deployment on **Render.com**.

1. Create a new **Web Service** on Render and connect this GitHub repository.
2. Set the **Build Command** to: `pip install -r requirements.txt`
3. Set the **Start Command** to: `gunicorn app:app`
4. Add all your `.env` variables in the **Environment Variables** tab.
5. Deploy!

---

## 📝 License
This project was developed by Muheem Akhtar. All rights reserved.

from flask import Flask
from dotenv import load_dotenv
from datetime import timedelta
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'campusconnect_super_secret_2024_xyz')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

from routes.auth import auth_bp
from routes.rides import rides_bp
from routes.hostels import hostels_bp
from routes.marketplace import marketplace_bp
from routes.messages import messages_bp
from routes.misc import misc_bp
from routes.new_features import new_bp

app.register_blueprint(auth_bp)
app.register_blueprint(rides_bp)
app.register_blueprint(hostels_bp)
app.register_blueprint(marketplace_bp)
app.register_blueprint(messages_bp)
app.register_blueprint(misc_bp)
app.register_blueprint(new_bp)

# ── Pakistan Standard Time filter (UTC → UTC+5) ──────────────────────────────
@app.template_filter('pkt')
def to_pkt(dt):
    """Convert a UTC datetime to Pakistan Standard Time (UTC+5)."""
    if dt is None:
        return None
    return dt + timedelta(hours=5)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
"""Fix all url_for calls in templates to use Blueprint prefixes."""
import os, re

REPLACEMENTS = [
    # Auth
    ("url_for('dashboard')",    "url_for('auth.dashboard')"),
    ("url_for('login')",        "url_for('auth.login')"),
    ("url_for('logout')",       "url_for('auth.logout')"),
    ("url_for('register')",     "url_for('auth.register')"),
    ("url_for('verify_otp')",   "url_for('auth.verify_otp')"),
    # Rides
    ("url_for('rides')",        "url_for('rides.rides')"),
    ("url_for('post_ride')",    "url_for('rides.post_ride')"),
    ("url_for('ride_detail',",  "url_for('rides.ride_detail',"),
    ("url_for('request_ride',", "url_for('rides.request_ride',"),
    ("url_for('accept_ride',",  "url_for('rides.accept_ride',"),
    ("url_for('reject_ride',",  "url_for('rides.reject_ride',"),
    ("url_for('delete_ride',",  "url_for('rides.delete_ride',"),
    # Hostels
    ("url_for('hostels')",      "url_for('hostels.hostels')"),
    ("url_for('post_hostel')",  "url_for('hostels.post_hostel')"),
    ("url_for('hostel_detail',","url_for('hostels.hostel_detail',"),
    ("url_for('bookmark_hostel',","url_for('hostels.bookmark_hostel',"),
    ("url_for('delete_hostel',","url_for('hostels.delete_hostel',"),
    # Marketplace
    ("url_for('marketplace')",  "url_for('marketplace.marketplace')"),
    ("url_for('post_item')",    "url_for('marketplace.post_item')"),
    ("url_for('item_detail',",  "url_for('marketplace.item_detail',"),
    ("url_for('delete_item',",  "url_for('marketplace.delete_item',"),
    ("url_for('report_item',",  "url_for('marketplace.report_item',"),
    ("url_for('add_review')",   "url_for('marketplace.add_review')"),
    # Messages
    ("url_for('messages')",     "url_for('messages.messages')"),
    ("url_for('chat',",         "url_for('messages.chat',"),
    # Misc
    ("url_for('notifications')", "url_for('misc.notifications')"),
    ("url_for('global_search')", "url_for('misc.global_search')"),
    ("url_for('profile')",       "url_for('misc.profile')"),
    ("url_for('edit_profile')",  "url_for('misc.edit_profile')"),
]

TEMPLATE_DIR = 'templates'
fixed = 0
for fname in os.listdir(TEMPLATE_DIR):
    if not fname.endswith('.html'):
        continue
    path = os.path.join(TEMPLATE_DIR, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)
    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {fname}")
        fixed += 1

print(f"\nDone. Fixed {fixed} template(s).")

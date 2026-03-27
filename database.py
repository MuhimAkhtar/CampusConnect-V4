import oracledb
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_PATH = os.path.join(BASE_DIR, 'wallet')

def get_connection():
    try:
        connection = oracledb.connect(
            user="ADMIN",
            password="AbujanAmijan@16",
            dsn="campusdb_low",            # 'low' is more stable for slow connections
            config_dir=WALLET_PATH,
            wallet_location=WALLET_PATH,
            wallet_password="AbujanAmijan@16"             # <--- Try empty first
        )
        print("Successfully connected to Oracle Cloud! 🚀")
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

if __name__ == "__main__":
    print("Connecting to Oracle Cloud... please wait ⏳")
    get_connection()
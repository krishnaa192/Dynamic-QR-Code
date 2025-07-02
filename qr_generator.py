import qrcode
import os
import sqlite3

DB_PATH = "qr_tracking.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS qr_links (
            id TEXT PRIMARY KEY,
            destination_url TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS qr_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_id TEXT,
            timestamp TEXT,
            ip_address TEXT,
            user_agent TEXT
        )''')

def generate_qr(qr_id, destination_url):
    init_db()  # Ensure DB tables exist before use

    qr_url = f"http://localhost:5000/qr?id={qr_id}"
    save_path = f"static/qr/{qr_id}.png"

    os.makedirs("static/qr", exist_ok=True)

    # Save QR image
    img = qrcode.make(qr_url)
    img.save(save_path)

    # Store in DB
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT OR REPLACE INTO qr_links (id, destination_url, active)
            VALUES (?, ?, 1)
        ''', (qr_id, destination_url))

    print(f"[✓] QR code '{qr_id}' created → {save_path}")

# Example usage
if __name__ == "__main__":
    generate_qr("promo1", "https://play.google.com/store/apps/details?id=com.crexin.bestbudget")

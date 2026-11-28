import sqlite3
import json
from abra.config import DB_PATH, ensure_dirs

def get_db():
    ensure_dirs()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY,
        name TEXT, phone TEXT, id_no TEXT,
        location TEXT, business TEXT,
        guarantor TEXT, g_phone TEXT,
        guarantor2 TEXT, next_kin TEXT,
        notes TEXT, photo TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY,
        client_id INTEGER, client_name TEXT,
        principal REAL, interest REAL, total REAL,
        paid REAL DEFAULT 0, balance REAL,
        plan TEXT, duration INTEGER, penalty REAL,
        collateral TEXT, date TEXT, due_date TEXT,
        receipt_no TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS cashbook (
        id INTEGER PRIMARY KEY,
        time TEXT, type TEXT, client TEXT,
        method TEXT, amount REAL, by_staff TEXT,
        note TEXT, loan_id INTEGER
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT
    )""")

    cur.execute("INSERT OR IGNORE INTO settings VALUES (?,?)",
        ("biz", json.dumps({
            "bizName": "ABRA FINANCES",
            "phone": "0770 000 000",
            "location": "Kampala, Uganda",
            "rate": 20, "penalty": 5,
            "footer": "Thank you for choosing ABRA FINANCES - Pay on time, borrow more!",
            "pin": "1234"
        })))

    conn.commit()
    conn.close()

import sqlite3
from datetime import datetime
from typing import Optional

class Database:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self.connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                radius INTEGER DEFAULT 50,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year INTEGER,
                make TEXT,
                model TEXT,
                price REAL NOT NULL,
                market_value REAL,
                repairs REAL DEFAULT 0,
                fees REAL DEFAULT 0,
                mileage INTEGER,
                city TEXT,
                state TEXT,
                source TEXT DEFAULT 'Manual',
                listing_url TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS market_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                state TEXT,
                make TEXT,
                model TEXT,
                sold_count INTEGER DEFAULT 0,
                bought_count INTEGER DEFAULT 0,
                avg_price REAL DEFAULT 0,
                avg_days_to_sell REAL DEFAULT 0,
                period_days INTEGER DEFAULT 30,
                updated_at TEXT NOT NULL
            );
            """)

    def upsert_user(self, telegram_id: int, city: str = "", state: str = "", zip_code: str = "", radius: int = 50):
        with self.connect() as conn:
            conn.execute("""
            INSERT INTO users (telegram_id, city, state, zip_code, radius, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                city=excluded.city, state=excluded.state,
                zip_code=excluded.zip_code, radius=excluded.radius
            """, (telegram_id, city, state, zip_code, radius, datetime.utcnow().isoformat()))

    def get_user(self, telegram_id: int):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()

    def add_deal(self, deal: dict):
        with self.connect() as conn:
            conn.execute("""
            INSERT INTO deals
            (title, year, make, model, price, market_value, repairs, fees,
             mileage, city, state, source, listing_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deal.get("title"), deal.get("year"), deal.get("make"), deal.get("model"),
                deal.get("price"), deal.get("market_value"), deal.get("repairs", 0),
                deal.get("fees", 0), deal.get("mileage"), deal.get("city"), deal.get("state"),
                deal.get("source", "Manual"), deal.get("listing_url"),
                datetime.utcnow().isoformat()
            ))

    def best_deals(self, city: Optional[str] = None, state: Optional[str] = None, limit: int = 10):
        query = """
        SELECT *,
          (COALESCE(market_value,0)-price-COALESCE(repairs,0)-COALESCE(fees,0)) AS profit
        FROM deals
        WHERE status='active'
        """
        args = []
        if state:
            query += " AND (state=? OR state IS NULL OR state='')"
            args.append(state)
        if city:
            query += " AND (city=? OR city IS NULL OR city='')"
            args.append(city)
        query += " ORDER BY profit DESC LIMIT ?"
        args.append(limit)
        with self.connect() as conn:
            return conn.execute(query, args).fetchall()

    def market_pulse(self, city: Optional[str], state: Optional[str], limit: int = 8):
        query = "SELECT * FROM market_stats WHERE 1=1"
        args = []
        if state:
            query += " AND state=?"
            args.append(state)
        if city:
            query += " AND city=?"
            args.append(city)
        query += " ORDER BY (sold_count+bought_count) DESC LIMIT ?"
        args.append(limit)
        with self.connect() as conn:
            return conn.execute(query, args).fetchall()

import sqlite3
import uuid
import os

class DatabaseRepository:
    """
    Technical Debt: Using SQLite for local demonstration.
    Upgrade path: PostgreSQL for production-grade FOR UPDATE SKIP LOCKED.
    """
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "terminator.db"))
        self._setup_schema()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _setup_schema(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS failed_transactions (
                    txn_id TEXT PRIMARY KEY, user_id TEXT, amount REAL, error_code TEXT,
                    status TEXT DEFAULT 'pending', retry_count INTEGER DEFAULT 0,
                    escalation_tier INTEGER DEFAULT 1, agent_context TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY, txn_id TEXT, action_taken TEXT, outcome TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(txn_id) REFERENCES failed_transactions(txn_id)
                );
            """)

    def fetch_and_lock_pending(self, limit=10):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("BEGIN EXCLUSIVE")
            records = cur.execute("SELECT * FROM failed_transactions WHERE status = 'pending' LIMIT ?", (limit,)).fetchall()
            if records:
                txn_ids = [r['txn_id'] for r in records]
                cur.execute(f"UPDATE failed_transactions SET status = 'processing' WHERE txn_id IN ({','.join('?'*len(txn_ids))})", txn_ids)
            return [dict(r) for r in records]

    def update_transaction(self, txn_id, status, retry_count, tier, context):
        with self.get_connection() as conn:
            conn.execute("UPDATE failed_transactions SET status=?, retry_count=?, escalation_tier=?, agent_context=? WHERE txn_id=?", 
                         (status, retry_count, tier, context, txn_id))

    def log_audit(self, txn_id, action, outcome):
        with self.get_connection() as conn:
            conn.execute("INSERT INTO audit_logs (log_id, txn_id, action_taken, outcome) VALUES (?, ?, ?, ?)", 
                         (str(uuid.uuid4()), txn_id, action, outcome))


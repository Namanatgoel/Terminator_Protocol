import sqlite3
import uuid
import os

class DatabaseRepository:
    """
    Technical Debt: Using SQLite for local demonstration.
    Upgrade path: PostgreSQL with FOR UPDATE SKIP LOCKED for production-grade concurrency.
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
                    log_id TEXT PRIMARY KEY,
                    txn_id TEXT,
                    amount REAL,
                    action_taken TEXT,
                    outcome TEXT,
                    ai_reasoning TEXT,
                    offer_authorized INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(txn_id) REFERENCES failed_transactions(txn_id)
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
            conn.execute(
                "UPDATE failed_transactions SET status=?, retry_count=?, escalation_tier=?, agent_context=? WHERE txn_id=?",
                (status, retry_count, tier, context, txn_id)
            )

    def log_audit(self, txn_id, amount, action, outcome, ai_reasoning="", offer_authorized=False):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO audit_logs (log_id, txn_id, amount, action_taken, outcome, ai_reasoning, offer_authorized) VALUES (?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), txn_id, amount, action, outcome, ai_reasoning, int(offer_authorized))
            )

    def recovery_report(self) -> dict:
        """Return ₹ recovered vs ₹ at-risk across the full batch."""
        with self.get_connection() as conn:
            total_at_risk = conn.execute("SELECT COALESCE(SUM(amount),0) FROM failed_transactions").fetchone()[0]
            total_lost = conn.execute("SELECT COALESCE(SUM(amount),0) FROM failed_transactions WHERE status='hard_failed'").fetchone()[0]
            total_in_flight = conn.execute("SELECT COALESCE(SUM(amount),0) FROM failed_transactions WHERE status IN ('pending','processing')").fetchone()[0]
            actions = conn.execute("SELECT action_taken, COUNT(*) as cnt, COALESCE(SUM(amount),0) as vol FROM audit_logs GROUP BY action_taken").fetchall()
        recovered = total_at_risk - total_lost - total_in_flight
        return {
            "total_at_risk": round(total_at_risk, 2),
            "recovered": round(recovered, 2),
            "lost": round(total_lost, 2),
            "in_flight": round(total_in_flight, 2),
            "recovery_rate_pct": round(100 * recovered / total_at_risk, 1) if total_at_risk else 0.0,
            "actions": [{"action": r["action_taken"], "count": r["cnt"], "volume": round(r["vol"], 2)} for r in actions],
        }


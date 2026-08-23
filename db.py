import sqlite3
import uuid
import os

# Ponytail ceiling: Using SQLite for local buildathon demonstration instead of Postgres.
# Upgrade path: Switch back to psycopg2 and asyncpg for production-grade FOR UPDATE SKIP LOCKED.
DB_PATH = os.path.join(os.path.dirname(__file__), "terminator.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_schema():
    """Idempotent schema creation."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS failed_transactions (
                txn_id TEXT PRIMARY KEY,
                user_id TEXT,
                amount REAL,
                error_code TEXT,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                escalation_tier INTEGER DEFAULT 1,
                agent_context TEXT DEFAULT ''
            );
            
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id TEXT PRIMARY KEY,
                txn_id TEXT,
                action_taken TEXT,
                outcome TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(txn_id) REFERENCES failed_transactions(txn_id)
            );
        """)
        conn.commit()

def fetch_and_lock_pending(limit=10):
    """Atomic fetch using standard SQLite transctions."""
    with get_connection() as conn:
        cur = conn.cursor()
        # SQLite doesn't have FOR UPDATE SKIP LOCKED, so we just do a quick transaction
        cur.execute("BEGIN EXCLUSIVE")
        cur.execute("""
            SELECT * FROM failed_transactions 
            WHERE status = 'pending' 
            LIMIT ?
        """, (limit,))
        records = cur.fetchall()
        
        if records:
            txn_ids = [r['txn_id'] for r in records]
            placeholders = ','.join('?' for _ in txn_ids)
            cur.execute(f"""
                UPDATE failed_transactions SET status = 'processing'
                WHERE txn_id IN ({placeholders})
            """, txn_ids)
        conn.commit()
        return [dict(r) for r in records]

def update_transaction(txn_id, status, retry_count, escalation_tier, agent_context):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE failed_transactions 
            SET status = ?, retry_count = ?, escalation_tier = ?, agent_context = ?
            WHERE txn_id = ?
        """, (status, retry_count, escalation_tier, agent_context, txn_id))
        conn.commit()

def log_audit(txn_id, action_taken, outcome):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_logs (log_id, txn_id, action_taken, outcome)
            VALUES (?, ?, ?, ?)
        """, (str(uuid.uuid4()), txn_id, action_taken, outcome))
        conn.commit()


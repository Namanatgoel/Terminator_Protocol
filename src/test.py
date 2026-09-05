import uuid
import csv
import random
import logging
from db import DatabaseRepository

logger = logging.getLogger("test")

def generate_synthetic_data(db: DatabaseRepository, count=50):
    """Checkpoint 1: Seed the DB with synthetic degraded-payment records."""
    error_codes = ["insufficient_funds", "checkout_abandoned", "card_declined"]
    with db.get_connection() as conn:
        for _ in range(count):
            conn.execute(
                "INSERT INTO failed_transactions (txn_id, user_id, amount, error_code) VALUES (?,?,?,?) ON CONFLICT DO NOTHING",
                (str(uuid.uuid4()), f"user_{random.randint(1000,9999)}", round(random.uniform(500, 50000), 2), random.choice(error_codes)),
            )
        conn.commit()  # BUG-FIX: sqlite3 context manager does NOT auto-commit DML on raw connections.
    logger.info(f"Seeded {count} synthetic failed transactions.")

def export_audit_log(db: DatabaseRepository, filename="audit_export.csv"):
    """Checkpoint 3: Export audit_logs to CSV for evaluator review."""
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM audit_logs").fetchall()
    if not rows:
        logger.info("No audit logs to export.")
        return
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows([dict(r) for r in rows])
    logger.info(f"Exported {len(rows)} audit log entries to {filename}.")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    db = DatabaseRepository()
    generate_synthetic_data(db)
    # Chaos test (Checkpoint 2): run executor.py and kill the network mid-run.


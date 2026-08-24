import uuid
import csv
import random
from db import DatabaseRepository

def generate_synthetic_data(db: DatabaseRepository, count=50):
    """Checkpoint 1: Generate 50 rows of degraded payment data."""
    error_codes = ['insufficient_funds', 'checkout_abandoned', 'card_declined']
    with db.get_connection() as conn:
        for _ in range(count):
            txn_id = str(uuid.uuid4())
            user_id = f"user_{random.randint(1000, 9999)}"
            amount = round(random.uniform(500, 50000), 2)
            error = random.choice(error_codes)
            
            conn.execute("""
                INSERT INTO failed_transactions (txn_id, user_id, amount, error_code)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (txn_id) DO NOTHING
            """, (txn_id, user_id, amount, error))
    print(f"Generated {count} synthetic failed transactions.")

def export_audit_log(db: DatabaseRepository, filename="audit_export.csv"):
    """Checkpoint 3: Export the audit_logs table."""
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM audit_logs").fetchall()
        if rows:
            keys = rows[0].keys()
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows([dict(row) for row in rows])
            print(f"Exported {len(rows)} audit logs to {filename}.")
        else:
            print("No audit logs found to export.")

if __name__ == "__main__":
    db = DatabaseRepository()
    generate_synthetic_data(db)
    # To run chaos test (Checkpoint 2), execute executor.py and manually kill the network.

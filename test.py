import uuid
import csv
import random
from db import setup_schema, get_connection

def generate_synthetic_data(count=50):
    """Checkpoint 1: Generate 50 rows of degraded payment data."""
    setup_schema() # Ensure schema exists
    
    error_codes = ['insufficient_funds', 'checkout_abandoned', 'card_declined']
    with get_connection() as conn:
        cur = conn.cursor()
        for _ in range(count):
            txn_id = str(uuid.uuid4())
            user_id = f"user_{random.randint(1000, 9999)}"
            amount = round(random.uniform(500, 50000), 2)
            error = random.choice(error_codes)
            
            cur.execute("""
                INSERT INTO failed_transactions (txn_id, user_id, amount, error_code)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (txn_id) DO NOTHING
            """, (txn_id, user_id, amount, error))
        conn.commit()
    print(f"Generated {count} synthetic failed transactions.")

def export_audit_log(filename="audit_export.csv"):
    """Checkpoint 3: Export the audit_logs table."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM audit_logs")
        rows = cur.fetchall()
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
    generate_synthetic_data()
    # To run chaos test (Checkpoint 2), we run executor.py and manually kill the network.

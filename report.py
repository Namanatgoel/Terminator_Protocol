"""
report.py - Recovery summary for the Terminator Protocol batch.
Usage: python report.py
"""
import logging
from db import DatabaseRepository

logging.basicConfig(level=logging.INFO)

def recovery_report(db: DatabaseRepository) -> dict:
    report = db.recovery_report()
    print("\n" + "═" * 52)
    print("  TERMINATOR PROTOCOL - RECOVERY REPORT")
    print("═" * 52)
    print(f"  Total at-risk :  ₹{report['total_at_risk']:>12,.2f}")
    print(f"  Recovered      :  ₹{report['recovered']:>12,.2f}  ({report['recovery_rate_pct']}%)")
    print(f"  In-flight      :  ₹{report['in_flight']:>12,.2f}")
    print(f"  Lost           :  ₹{report['lost']:>12,.2f}")
    print("─" * 52)
    print("  Actions taken:")
    for a in report["actions"]:
        print(f"    {a['action']:<20} {a['count']:>4} events   ₹{a['volume']:>10,.2f}")
    print("═" * 52 + "\n")
    return report

if __name__ == "__main__":
    recovery_report(DatabaseRepository())

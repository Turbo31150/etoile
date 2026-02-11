"""Temp script to inspect trades table schema."""
import sqlite3

db_path = "F:/BUREAU/carV1/database/trading_latest.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("PRAGMA table_info(trades)")
print("Schema trades:")
for col in c.fetchall():
    print(f"  {col}")

# Check high score signals
c.execute("SELECT symbol, direction, price, score, tp1, sl, created_at FROM signals WHERE score >= 70 ORDER BY created_at DESC LIMIT 5")
rows = c.fetchall()
print(f"\nHigh score signals (>=70): {len(rows)}")
for r in rows:
    print(f"  {r}")

c.execute("SELECT COUNT(*) FROM signals WHERE score >= 70")
print(f"Total high score: {c.fetchone()[0]}")

conn.close()

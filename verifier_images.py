from dotenv import load_dotenv
import os

from sqlalchemy import create_engine, text

load_dotenv()

db_url = os.getenv("SUPABASE_DB_URL")

engine = create_engine(db_url)

with engine.connect() as conn:

    rows = conn.execute(
        text("""
            SELECT
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'order_items'
            ORDER BY ordinal_position
        """)
    ).fetchall()

    print()
    print("COLONNES DE LA TABLE ORDER_ITEMS")
    print("--------------------------------")

    for row in rows:
        print(
            f"{row[0]} | "
            f"{row[1]} | "
            f"NULL autorisé : {row[2]}"
        )
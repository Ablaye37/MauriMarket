from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

load_dotenv()

url = os.getenv("SUPABASE_DB_URL")

if not url:
    print("❌ SUPABASE_DB_URL manquant")
    exit()

engine = create_engine(url)

with engine.connect() as connection:

    rows = connection.execute(
        text("""
            SELECT
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'products'
            ORDER BY ordinal_position
        """)
    ).fetchall()

    print()
    print("COLONNES DE LA TABLE PRODUCTS")
    print("--------------------------------")

    for row in rows:
        print(
            f"{row[0]} | {row[1]} | NULL autorisé : {row[2]}"
        )
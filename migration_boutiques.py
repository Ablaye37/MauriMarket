import sqlite3

DB_NAME = "maurimarket.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# 1. Créer la table boutiques
cursor.execute("""
CREATE TABLE IF NOT EXISTS boutiques (
    id INTEGER PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    sale_type VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

# 2. Ajouter boutique_id à products s'il n'existe pas encore
columns = cursor.execute("PRAGMA table_info(products)").fetchall()
column_names = [column[1] for column in columns]

if "boutique_id" not in column_names:
    cursor.execute("""
    ALTER TABLE products
    ADD COLUMN boutique_id INTEGER
    """)

conn.commit()
conn.close()

print("✅ Migration Boutique terminée avec succès !")
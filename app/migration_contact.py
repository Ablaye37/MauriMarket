from app.database.database import engine
from sqlalchemy import text


def migrate_contact():

    print("🔄 Vérification de la table contact_messages...")

    with engine.begin() as connection:

        # Ajouter email s'il n'existe pas
        connection.execute(text("""
            ALTER TABLE contact_messages
            ADD COLUMN IF NOT EXISTS email VARCHAR(150)
        """))

        print("✅ Colonne email vérifiée/ajoutée.")

    print("✅ Migration contact terminée.")


if __name__ == "__main__":
    migrate_contact()
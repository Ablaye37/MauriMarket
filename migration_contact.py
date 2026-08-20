from app.database.database import engine
from sqlalchemy import text


def migrate_contact():

    print("Verification de la table contact_messages...")

    with engine.begin() as connection:

        # =====================================================
        # EMAIL
        # =====================================================

        connection.execute(text("""
            ALTER TABLE contact_messages
            ADD COLUMN IF NOT EXISTS email VARCHAR(150)
        """))

        print("Colonne email verifiee/ajoutee.")

        # =====================================================
        # STATUS
        # =====================================================

        connection.execute(text("""
            ALTER TABLE contact_messages
            ADD COLUMN IF NOT EXISTS status VARCHAR(20)
        """))

        connection.execute(text("""
            UPDATE contact_messages
            SET status = 'new'
            WHERE status IS NULL
        """))

        connection.execute(text("""
            ALTER TABLE contact_messages
            ALTER COLUMN status SET DEFAULT 'new'
        """))

        connection.execute(text("""
            ALTER TABLE contact_messages
            ALTER COLUMN status SET NOT NULL
        """))

        print("Colonne status configuree.")

        # =====================================================
        # CREATED_AT
        # =====================================================

        connection.execute(text("""
            ALTER TABLE contact_messages
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
        """))

        # Donner une date aux anciens messages
        connection.execute(text("""
            UPDATE contact_messages
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
        """))

        # Date automatique pour les nouveaux messages
        connection.execute(text("""
            ALTER TABLE contact_messages
            ALTER COLUMN created_at
            SET DEFAULT CURRENT_TIMESTAMP
        """))

        # Empêcher NULL
        connection.execute(text("""
            ALTER TABLE contact_messages
            ALTER COLUMN created_at SET NOT NULL
        """))

        print("Colonne created_at configuree.")

    print("Migration contact terminee.")


if __name__ == "__main__":
    migrate_contact()
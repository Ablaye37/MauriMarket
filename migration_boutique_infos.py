from sqlalchemy import text

from app.database.database import engine


def migration():

    print("==========================================")
    print("MIGRATION BOUTIQUE")
    print("==========================================")

    with engine.begin() as connection:

        colonnes = {
            "description": "TEXT",
            "city": "VARCHAR(100)",
            "logo": "VARCHAR(500)",
            "cover_image": "VARCHAR(500)"
        }

        for nom, type_colonne in colonnes.items():

            try:

                connection.execute(
                    text(
                        f"""
                        ALTER TABLE boutiques
                        ADD COLUMN IF NOT EXISTS
                        {nom} {type_colonne}
                        """
                    )
                )

                print(
                    f"✅ Colonne vérifiée : {nom}"
                )

            except Exception as e:

                print(
                    f"❌ Erreur pour {nom} :",
                    repr(e)
                )

    print("==========================================")
    print("✅ MIGRATION TERMINÉE")
    print("==========================================")


if __name__ == "__main__":
    migration()
import logging

from app.database.database import engine


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# DATABASE STARTUP
# ============================================================

def init_database():
    """
    Ancienne fonction de création automatique des tables.

    IMPORTANT :
    Les tables NE SONT PLUS créées automatiquement au démarrage.

    Le schéma de production doit être géré par les migrations
    ou directement dans Supabase.

    Cette fonction est conservée pour éviter de casser
    d'éventuels imports existants dans le projet.
    """

    logger.info(
        "Base de données : initialisation automatique désactivée."
    )

    logger.info(
        "Le schéma PostgreSQL/Supabase est géré par les migrations."
    )


# ============================================================
# OPTIONAL DATABASE CHECK
# ============================================================

def check_database_connection():
    """
    Vérifie manuellement la connexion à la base.

    Cette fonction n'est PAS appelée automatiquement par main.py.
    Elle peut être utilisée pour un diagnostic.
    """

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")

        logger.info(
            "Connexion à la base de données OK."
        )

        return True

    except Exception as exc:
        logger.error(
            "Connexion à la base de données impossible : %s",
            exc,
        )

        return False
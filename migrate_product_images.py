import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client
from sqlalchemy import text

from app.database.database import engine


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SUPABASE_BUCKET = "product-images"

UPLOAD_DIR = Path(
    "app/static/uploads/products"
)


# ============================================================
# VÉRIFICATIONS
# ============================================================

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL ou SUPABASE_KEY manquant.")
    raise SystemExit(1)

if not UPLOAD_DIR.exists():
    print(
        "❌ Dossier introuvable :",
        UPLOAD_DIR
    )
    raise SystemExit(1)


# ============================================================
# SUPABASE
# ============================================================

try:

    supabase = create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )

    print("✅ Client Supabase initialisé.")
    print(
        "✅ Bucket :",
        SUPABASE_BUCKET
    )

except Exception as e:

    print(
        "❌ Erreur initialisation Supabase :",
        repr(e)
    )

    raise SystemExit(1)


# ============================================================
# RÉCUPÉRER LES PRODUITS À MIGRER
# ============================================================

try:

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT id, image
                FROM products
                WHERE image LIKE '/static/uploads/products/%'
            """)
        )

        products = result.fetchall()


except Exception as e:

    print(
        "❌ Erreur lecture de la base :",
        repr(e)
    )

    raise SystemExit(1)


print()
print("==========================================")
print(
    "PRODUITS À MIGRER :",
    len(products)
)
print("==========================================")
print()


if not products:

    print(
        "ℹ️ Aucun ancien produit à migrer."
    )

    raise SystemExit(0)


migrated = 0
skipped = 0
errors = 0


# ============================================================
# MIGRATION
# ============================================================

for product_id, old_image in products:

    print("------------------------------------------")

    print(
        "Produit ID :",
        product_id
    )

    print(
        "Ancienne image :",
        old_image
    )


    # --------------------------------------------------------
    # Nom du fichier
    # --------------------------------------------------------

    filename = Path(
        old_image
    ).name

    local_file = (
        UPLOAD_DIR / filename
    )


    # --------------------------------------------------------
    # Vérifier le fichier local
    # --------------------------------------------------------

    if not local_file.exists():

        print(
            "⚠️ Fichier introuvable :",
            local_file
        )

        skipped += 1

        continue


    # --------------------------------------------------------
    # Lire l'image
    # --------------------------------------------------------

    try:

        content = local_file.read_bytes()

    except Exception as e:

        print(
            "❌ Impossible de lire le fichier :",
            repr(e)
        )

        errors += 1

        continue


    if not content:

        print(
            "⚠️ Fichier vide."
        )

        skipped += 1

        continue


    # --------------------------------------------------------
    # Type MIME
    # --------------------------------------------------------

    extension = (
        local_file.suffix.lower()
    )

    content_type = {

        ".jpg":
            "image/jpeg",

        ".jpeg":
            "image/jpeg",

        ".png":
            "image/png",

        ".webp":
            "image/webp",

    }.get(
        extension,
        "application/octet-stream"
    )


    # --------------------------------------------------------
    # Upload Supabase
    # --------------------------------------------------------

    try:

        supabase.storage \
            .from_(SUPABASE_BUCKET) \
            .upload(

                path=filename,

                file=content,

                file_options={

                    "content-type":
                        content_type,

                    "cache-control":
                        "3600",

                    "upsert":
                        "true"

                }

            )

        print(
            "✅ Image envoyée sur Supabase."
        )


    except Exception as e:

        print(
            "❌ Erreur upload :",
            repr(e)
        )

        errors += 1

        continue


    # --------------------------------------------------------
    # URL publique
    # --------------------------------------------------------

    try:

        public_url = (
            supabase
            .storage
            .from_(SUPABASE_BUCKET)
            .get_public_url(
                filename
            )
        )

        print(
            "✅ URL Supabase :",
            public_url
        )


    except Exception as e:

        print(
            "❌ Erreur récupération URL :",
            repr(e)
        )

        errors += 1

        continue


    # --------------------------------------------------------
    # Mise à jour directe de la DB
    # --------------------------------------------------------

    try:

        with engine.begin() as connection:

            connection.execute(

                text("""
                    UPDATE products
                    SET image = :image
                    WHERE id = :product_id
                """),

                {
                    "image":
                        public_url,

                    "product_id":
                        product_id
                }

            )


        print(
            "✅ Base de données mise à jour."
        )

        migrated += 1


    except Exception as e:

        print(
            "❌ Erreur mise à jour DB :",
            repr(e)
        )

        errors += 1

        continue


# ============================================================
# RÉSUMÉ
# ============================================================

print()

print("==========================================")
print("MIGRATION TERMINÉE")
print("==========================================")

print(
    "✅ Migrés :",
    migrated
)

print(
    "⚠️ Ignorés :",
    skipped
)

print(
    "❌ Erreurs :",
    errors
)

print("==========================================")

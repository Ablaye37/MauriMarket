from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal

from app.models.product import Product
from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.boutique import Boutique

from supabase import create_client

import os
import uuid
import traceback


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# CONFIGURATION SUPABASE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

BUCKET_NAME = "product-images"


supabase = None

if SUPABASE_URL and SUPABASE_KEY:

    try:

        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        print(
            "✅ Client Supabase initialisé"
        )

        print(
            "✅ Bucket images produits :",
            BUCKET_NAME
        )

    except Exception as e:

        print(
            "❌ ERREUR INITIALISATION SUPABASE :",
            repr(e)
        )

else:

    print(
        "❌ SUPABASE_URL ou SUPABASE_KEY manquant."
    )


# ============================================================
# CONTEXTE GLOBAL
# ============================================================

def get_global_context(
    request: Request,
    db
):

    user_id = request.session.get(
        "user_id"
    )

    user_name = request.session.get(
        "user_name"
    )

    panier = request.session.get(
        "panier",
        []
    )

    boutique = None

    if user_id:

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

    return {

        "user_name": user_name,

        "user_id": user_id,

        "panier_count": len(panier),

        "lang": request.query_params.get(
            "lang",
            "fr"
        ),

        "has_boutique":
            boutique is not None,

        "boutique":
            boutique
    }


# ============================================================
# CATÉGORIES
# ============================================================

def get_categories(db):

    return (
        db.query(Category)
        .order_by(
            Category.name.asc()
        )
        .all()
    )


# ============================================================
# SOUS-CATÉGORIES
# ============================================================

def get_subcategories(db):

    return (
        db.query(SubCategory)
        .order_by(
            SubCategory.name.asc()
        )
        .all()
    )


# ============================================================
# SAUVEGARDER IMAGE SUR SUPABASE
#
# IMPORTANT :
# AUCUNE IMAGE PRODUIT N'EST SAUVEGARDÉE
# SUR LE DISQUE LOCAL DE RAILWAY.
#
# TOUT PASSE PAR SUPABASE STORAGE.
# ============================================================

async def save_product_image(
    image: UploadFile
):

    # --------------------------------------------------------
    # AUCUNE IMAGE
    # --------------------------------------------------------

    if not image or not image.filename:

        print(
            "ℹ️ Aucun fichier image fourni."
        )

        return None


    # --------------------------------------------------------
    # VÉRIFIER SUPABASE
    # --------------------------------------------------------

    if not supabase:

        print(
            "❌ Supabase n'est pas configuré."
        )

        return None


    # --------------------------------------------------------
    # TYPES AUTORISÉS
    # --------------------------------------------------------

    allowed_types = {

        "image/jpeg": ".jpg",

        "image/png": ".png",

        "image/webp": ".webp"
    }


    extension = allowed_types.get(
        image.content_type
    )


    if not extension:

        print(
            "❌ Type d'image non autorisé :",
            image.content_type
        )

        return None


    # --------------------------------------------------------
    # LIRE IMAGE
    # --------------------------------------------------------

    content = await image.read()


    if not content:

        print(
            "❌ Image vide."
        )

        return None


    # --------------------------------------------------------
    # NOM UNIQUE
    # --------------------------------------------------------

    filename = (
        f"product_"
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )


    # --------------------------------------------------------
    # CHEMIN DANS SUPABASE
    # --------------------------------------------------------

    file_path = filename


    # --------------------------------------------------------
    # UPLOAD SUPABASE
    # --------------------------------------------------------

    try:

        supabase.storage \
            .from_(BUCKET_NAME) \
            .upload(

                path=file_path,

                file=content,

                file_options={

                    "content-type":
                        image.content_type,

                    "cache-control":
                        "3600",

                    "upsert":
                        "false"
                }
            )


        print(
            "=========================================="
        )

        print(
            "✅ IMAGE ENVOYÉE SUR SUPABASE"
        )

        print(
            "BUCKET :",
            BUCKET_NAME
        )

        print(
            "FICHIER :",
            file_path
        )

        print(
            "=========================================="
        )


    except Exception as e:

        print(
            "=========================================="
        )

        print(
            "❌ ERREUR UPLOAD SUPABASE"
        )

        print(
            "TYPE :",
            type(e).__name__
        )

        print(
            "ERREUR :",
            str(e)
        )

        print(
            "=========================================="
        )

        return None


    # --------------------------------------------------------
    # RÉCUPÉRER URL PUBLIQUE
    # --------------------------------------------------------

    try:

        public_url = (
            supabase
            .storage
            .from_(BUCKET_NAME)
            .get_public_url(
                file_path
            )
        )


        print(
            "✅ URL IMAGE SUPABASE :",
            public_url
        )


        return public_url


    except Exception as e:

        print(
            "❌ ERREUR URL SUPABASE :",
            repr(e)
        )

        return None


# ============================================================
# VÉRIFIER CATÉGORIE + SOUS-CATÉGORIE
# ============================================================

def validate_category_and_subcategory(
    db,
    category_id: int,
    subcategory_id: int
):

    # --------------------------------------------------------
    # CATÉGORIE
    # --------------------------------------------------------

    category = (
        db.query(Category)
        .filter(
            Category.id == category_id
        )
        .first()
    )


    if not category:

        return None, None


    # --------------------------------------------------------
    # SOUS-CATÉGORIE
    # --------------------------------------------------------

    subcategory = (
        db.query(SubCategory)
        .filter(
            SubCategory.id == subcategory_id
        )
        .first()
    )


    if not subcategory:

        return None, None


    # --------------------------------------------------------
    # VÉRIFIER RELATION
    # --------------------------------------------------------

    if (
        subcategory.category_id
        != category_id
    ):

        print(
            "❌ Sous-catégorie incompatible."
        )

        print(
            "Catégorie sélectionnée :",
            category_id
        )

        print(
            "Catégorie de la sous-catégorie :",
            subcategory.category_id
        )

        return None, None


    return category, subcategory


# ============================================================
# PUBLIER DEPUIS L'ACCUEIL
# GET /publier
# ============================================================

@router.get("/publier")
async def publish_page(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )


    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )


    db = SessionLocal()


    try:

        categories = get_categories(
            db
        )

        subcategories = get_subcategories(
            db
        )

        global_context = get_global_context(
            request,
            db
        )


        return templates.TemplateResponse(

            request=request,

            name="publier.html",

            context={

                "categories":
                    categories,

                "subcategories":
                    subcategories,

                "is_boutique_publish":
                    False,

                **global_context
            }
        )


    except Exception as e:

        print(
            "ERREUR GET /publier :",
            repr(e)
        )

        traceback.print_exc()


        return RedirectResponse(
            "/",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# PUBLIER DEPUIS MA BOUTIQUE
# GET /ma-boutique/publier
# ============================================================

@router.get("/ma-boutique/publier")
async def publish_boutique_page(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )


    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )


    db = SessionLocal()


    try:

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )


        if not boutique:

            return RedirectResponse(
                "/boutique/creer",
                status_code=303
            )


        categories = get_categories(
            db
        )

        subcategories = get_subcategories(
            db
        )

        global_context = get_global_context(
            request,
            db
        )


        return templates.TemplateResponse(

            request=request,

            name="publier.html",

            context={

                "categories":
                    categories,

                "subcategories":
                    subcategories,

                "boutique":
                    boutique,

                "is_boutique_publish":
                    True,

                **global_context
            }
        )


    except Exception as e:

        print(
            "ERREUR GET /ma-boutique/publier :",
            repr(e)
        )

        traceback.print_exc()


        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# TRAITEMENT PUBLICATION ACCUEIL
# POST /publier
#
# Produit indépendant
# boutique_id = None
# ============================================================

@router.post("/publier")
async def publish_product(

    request: Request,

    title: str = Form(...),

    description: str = Form(...),

    price: float = Form(...),

    city: str = Form(...),

    condition: str = Form(...),

    category_id: int = Form(...),

    subcategory_id: int = Form(...),

    image: UploadFile = File(None)

):

    user_id = request.session.get(
        "user_id"
    )


    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )


    db = SessionLocal()


    try:

        # ----------------------------------------------------
        # NETTOYAGE
        # ----------------------------------------------------

        title = title.strip()

        description = description.strip()

        city = city.strip()

        condition = condition.strip()


        # ----------------------------------------------------
        # VÉRIFIER CATÉGORIE
        # ----------------------------------------------------

        category, subcategory = (
            validate_category_and_subcategory(
                db,
                category_id,
                subcategory_id
            )
        )


        if not category or not subcategory:

            return RedirectResponse(
                "/publier",
                status_code=303
            )


        # ----------------------------------------------------
        # IMAGE SUPABASE
        # ----------------------------------------------------

        image_path = await save_product_image(
            image
        )


        # ----------------------------------------------------
        # CRÉER PRODUIT INDÉPENDANT
        # ----------------------------------------------------

        product = Product(

            title=title,

            description=description,

            price=price,

            city=city,

            condition=condition,

            category_id=category_id,

            subcategory_id=subcategory_id,

            user_id=user_id,

            image=image_path,

            boutique_id=None
        )


        db.add(product)

        db.commit()

        db.refresh(product)


        print(
            "=========================================="
        )

        print(
            "✅ PRODUIT PUBLIÉ INDÉPENDANT"
        )

        print(
            "ID :",
            product.id
        )

        print(
            "IMAGE :",
            product.image
        )

        print(
            "CATÉGORIE ID :",
            product.category_id
        )

        print(
            "SOUS-CATÉGORIE ID :",
            product.subcategory_id
        )

        print(
            "BOUTIQUE ID :",
            product.boutique_id
        )

        print(
            "=========================================="
        )


        return RedirectResponse(
            "/",
            status_code=303
        )


    except Exception as e:

        db.rollback()


        print(
            "=========================================="
        )

        print(
            "❌ ERREUR PUBLICATION"
        )

        print(
            "TYPE :",
            type(e).__name__
        )

        print(
            "ERREUR :",
            str(e)
        )

        traceback.print_exc()

        print(
            "=========================================="
        )


        return RedirectResponse(
            "/publier",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# TRAITEMENT PUBLICATION MA BOUTIQUE
# POST /ma-boutique/publier
#
# Produit appartenant à la boutique du vendeur
# boutique_id = boutique.id
# ============================================================

@router.post("/ma-boutique/publier")
async def publish_boutique_product(

    request: Request,

    title: str = Form(...),

    description: str = Form(...),

    price: float = Form(...),

    city: str = Form(...),

    condition: str = Form(...),

    category_id: int = Form(...),

    subcategory_id: int = Form(...),

    image: UploadFile = File(None)

):

    user_id = request.session.get(
        "user_id"
    )


    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )


    db = SessionLocal()


    try:

        # ----------------------------------------------------
        # RÉCUPÉRER LA BOUTIQUE DU VENDEUR
        # ----------------------------------------------------

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )


        if not boutique:

            return RedirectResponse(
                "/boutique/creer",
                status_code=303
            )


        # ----------------------------------------------------
        # NETTOYAGE
        # ----------------------------------------------------

        title = title.strip()

        description = description.strip()

        city = city.strip()

        condition = condition.strip()


        # ----------------------------------------------------
        # VÉRIFIER CATÉGORIE
        # ----------------------------------------------------

        category, subcategory = (
            validate_category_and_subcategory(
                db,
                category_id,
                subcategory_id
            )
        )


        if not category or not subcategory:

            return RedirectResponse(
                "/ma-boutique/publier",
                status_code=303
            )


        # ----------------------------------------------------
        # IMAGE SUPABASE
        # ----------------------------------------------------

        image_path = await save_product_image(
            image
        )


        # ----------------------------------------------------
        # CRÉER PRODUIT DANS LA BOUTIQUE
        # ----------------------------------------------------

        product = Product(

            title=title,

            description=description,

            price=price,

            city=city,

            condition=condition,

            category_id=category_id,

            subcategory_id=subcategory_id,

            user_id=user_id,

            image=image_path,

            boutique_id=boutique.id
        )


        db.add(product)

        db.commit()

        db.refresh(product)


        print(
            "=========================================="
        )

        print(
            "✅ PRODUIT PUBLIÉ DANS MA BOUTIQUE"
        )

        print(
            "PRODUIT ID :",
            product.id
        )

        print(
            "IMAGE :",
            product.image
        )

        print(
            "BOUTIQUE ID :",
            boutique.id
        )

        print(
            "BOUTIQUE :",
            boutique.name
        )

        print(
            "CATÉGORIE ID :",
            product.category_id
        )

        print(
            "SOUS-CATÉGORIE ID :",
            product.subcategory_id
        )

        print(
            "=========================================="
        )


        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )


    except Exception as e:

        db.rollback()


        print(
            "=========================================="
        )

        print(
            "❌ ERREUR PUBLICATION BOUTIQUE"
        )

        print(
            "TYPE :",
            type(e).__name__
        )

        print(
            "ERREUR :",
            str(e)
        )

        traceback.print_exc()

        print(
            "=========================================="
        )


        return RedirectResponse(
            "/ma-boutique/publier",
            status_code=303
        )


    finally:

        db.close()

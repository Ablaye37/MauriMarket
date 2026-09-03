
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal

from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.boutique import Boutique

from supabase import create_client

import os
import uuid
import traceback


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# CONFIGURATION SUPABASE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

BUCKET_NAME = "product-images"

supabase = None


if SUPABASE_URL and SUPABASE_KEY:

    try:

        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        print("==========================================")
        print("[OK] CLIENT SUPABASE INITIALISE")
        print("[OK] BUCKET :", BUCKET_NAME)
        print("==========================================")

    except Exception as e:

        print("==========================================")
        print("[ERREUR] ERREUR INITIALISATION SUPABASE")
        print("TYPE :", type(e).__name__)
        print("ERREUR :", str(e))
        print("==========================================")

        traceback.print_exc()

else:

    print("==========================================")
    print("[ERREUR] SUPABASE_URL OU SUPABASE_KEY MANQUANT")
    print("==========================================")


# ============================================================
# CONVERSION LIVRAISON
# ============================================================

def parse_delivery(value):
    """
    Convertit la valeur envoyée par le formulaire
    en booléen.
    """

    print(
        "📦 VALEUR LIVRAISON BRUTE :",
        repr(value)
    )

    if value is None:

        print(
            "📦 Aucune valeur de livraison reçue -> False"
        )

        return False

    if isinstance(value, bool):

        print(
            "📦 Valeur déjà booléenne :",
            value
        )

        return value

    value = str(value).strip().lower()

    result = value in (
        "true",
        "1",
        "yes",
        "oui",
        "on"
    )

    print(
        "📦 VALEUR LIVRAISON CONVERTIE :",
        result
    )

    return result


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

        "has_boutique": (
            boutique is not None
        ),

        "boutique": boutique
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
            "[ERREUR] SUPABASE NON CONFIGURE"
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
            "[ERREUR] TYPE D'IMAGE NON AUTORISE :",
            image.content_type
        )

        return None


    # --------------------------------------------------------
    # LIRE IMAGE
    # --------------------------------------------------------

    try:

        content = await image.read()

    except Exception as e:

        print(
            "❌ ERREUR LECTURE IMAGE :",
            repr(e)
        )

        traceback.print_exc()

        return None


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

    file_path = filename


    # --------------------------------------------------------
    # UPLOAD SUPABASE
    # --------------------------------------------------------

    try:

        (
            supabase
            .storage
            .from_(BUCKET_NAME)
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
        )


        print(
            "=========================================="
        )

        print(
            "✅ IMAGE PRODUIT ENVOYÉE SUR SUPABASE"
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

        traceback.print_exc()

        return None


    # --------------------------------------------------------
    # URL PUBLIQUE
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

        traceback.print_exc()

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

        print(
            "❌ Catégorie inexistante :",
            category_id
        )

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

        print(
            "❌ Sous-catégorie inexistante :",
            subcategory_id
        )

        return None, None


    # --------------------------------------------------------
    # VÉRIFIER RELATION
    # --------------------------------------------------------

    if subcategory.category_id != category_id:

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
            "=========================================="
        )

        print(
            "❌ ERREUR GET /publier"
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
            "=========================================="
        )

        print(
            "❌ ERREUR GET /ma-boutique/publier"
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

    delivery_available: str | None = Form(None),

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
        # VALIDATION TITRE
        # ----------------------------------------------------

        if not title:

            request.session["message"] = (
                "❌ Le titre est obligatoire."
            )

            return RedirectResponse(
                "/publier",
                status_code=303
            )


        # ----------------------------------------------------
        # VALIDATION PRIX
        # ----------------------------------------------------

        if price < 0:

            request.session["message"] = (
                "❌ Le prix ne peut pas être négatif."
            )

            return RedirectResponse(
                "/publier",
                status_code=303
            )


        # ----------------------------------------------------
        # LIVRAISON
        # ----------------------------------------------------

        delivery_available_bool = parse_delivery(
            delivery_available
        )


        print(
            "=========================================="
        )

        print(
            "📦 PUBLICATION PRODUIT"
        )

        print(
            "📦 DELIVERY REÇU :",
            repr(delivery_available)
        )

        print(
            "📦 DELIVERY FINAL :",
            delivery_available_bool
        )

        print(
            "=========================================="
        )


        # ----------------------------------------------------
        # CATÉGORIE + SOUS-CATÉGORIE
        # ----------------------------------------------------

        category, subcategory = (
            validate_category_and_subcategory(
                db,
                category_id,
                subcategory_id
            )
        )


        if not category or not subcategory:

            request.session["message"] = (
                "❌ Catégorie ou sous-catégorie invalide."
            )

            return RedirectResponse(
                "/publier",
                status_code=303
            )


        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        image_path = await save_product_image(
            image
        )


        # ----------------------------------------------------
        # CRÉER PRODUIT
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

            boutique_id=None,

            delivery_available=(
                delivery_available_bool
            )
        )


        # ----------------------------------------------------
        # SAUVEGARDE
        # ----------------------------------------------------

        db.add(product)

        db.commit()

        db.refresh(product)


        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        print(
            "=========================================="
        )

        print(
            "✅ PRODUIT PUBLIÉ"
        )

        print(
            "ID :",
            product.id
        )

        print(
            "TITRE :",
            product.title
        )

        print(
            "IMAGE :",
            product.image
        )

        print(
            "LIVRAISON :",
            product.delivery_available
        )

        print(
            "BOUTIQUE ID :",
            product.boutique_id
        )

        print(
            "=========================================="
        )


        request.session["message"] = (
            f"✅ Produit « {product.title} » "
            "publié avec succès."
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


        request.session["message"] = (
            "❌ Impossible de publier le produit."
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
# Produit appartenant à la boutique
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

    delivery_available: str | None = Form(None),

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
        # RÉCUPÉRER LA BOUTIQUE
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
        # VALIDATION TITRE
        # ----------------------------------------------------

        if not title:

            request.session["message"] = (
                "❌ Le titre est obligatoire."
            )

            return RedirectResponse(
                "/ma-boutique/publier",
                status_code=303
            )


        # ----------------------------------------------------
        # VALIDATION PRIX
        # ----------------------------------------------------

        if price < 0:

            request.session["message"] = (
                "❌ Le prix ne peut pas être négatif."
            )

            return RedirectResponse(
                "/ma-boutique/publier",
                status_code=303
            )


        # ----------------------------------------------------
        # LIVRAISON
        # ----------------------------------------------------

        delivery_available_bool = parse_delivery(
            delivery_available
        )


        print(
            "=========================================="
        )

        print(
            "📦 PUBLICATION PRODUIT BOUTIQUE"
        )

        print(
            "📦 DELIVERY REÇU :",
            repr(delivery_available)
        )

        print(
            "📦 DELIVERY FINAL :",
            delivery_available_bool
        )

        print(
            "=========================================="
        )


        # ----------------------------------------------------
        # CATÉGORIE + SOUS-CATÉGORIE
        # ----------------------------------------------------

        category, subcategory = (
            validate_category_and_subcategory(
                db,
                category_id,
                subcategory_id
            )
        )


        if not category or not subcategory:

            request.session["message"] = (
                "❌ Catégorie ou sous-catégorie invalide."
            )

            return RedirectResponse(
                "/ma-boutique/publier",
                status_code=303
            )


        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        image_path = await save_product_image(
            image
        )


        # ----------------------------------------------------
        # CRÉER PRODUIT
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

            boutique_id=boutique.id,

            delivery_available=(
                delivery_available_bool
            )
        )


        # ----------------------------------------------------
        # SAUVEGARDE
        # ----------------------------------------------------

        db.add(product)

        db.commit()

        db.refresh(product)


        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

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
            "BOUTIQUE ID :",
            boutique.id
        )

        print(
            "BOUTIQUE :",
            boutique.name
        )

        print(
            "IMAGE :",
            product.image
        )

        print(
            "LIVRAISON :",
            product.delivery_available
        )

        print(
            "=========================================="
        )


        request.session["message"] = (
            f"✅ Produit « {product.title} » "
            "publié dans votre boutique."
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


        request.session["message"] = (
            "❌ Impossible de publier le produit "
            "dans la boutique."
        )


        return RedirectResponse(
            "/ma-boutique/publier",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# MES ANNONCES
#
# Affiche uniquement les produits indépendants
# de l'utilisateur.
#
# boutique_id = None
# ============================================================

@router.get("/mes-annonces")
async def mes_annonces(
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

        products = (
            db.query(Product)
            .filter(

                Product.user_id == user_id,

                Product.boutique_id == None,

                Product.is_active == True
            )
            .order_by(
                Product.id.desc()
            )
            .all()
        )


        global_context = get_global_context(
            request,
            db
        )


        return templates.TemplateResponse(

            request=request,

            name="mes_annonces.html",

            context={

                "products":
                    products,

                "annonces":
                    products,

                **global_context
            }
        )


    except Exception as e:

        print(
            "=========================================="
        )

        print(
            "❌ ERREUR /mes-annonces"
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
            "/",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# MODIFIER UNE ANNONCE
# GET /annonce/modifier/{product_id}
# ============================================================

@router.get("/annonce/modifier/{product_id}")
async def modifier_annonce_page(

    request: Request,

    product_id: int

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

        product = (
            db.query(Product)
            .filter(

                Product.id == product_id,

                Product.user_id == user_id,

                Product.is_active == True
            )
            .first()
        )


        if not product:

            request.session["message"] = (
                "❌ Annonce introuvable ou accès refusé."
            )


            return RedirectResponse(
                "/mes-annonces",
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

            name="modifier_produit.html",

            context={

                "product":
                    product,

                "categories":
                    categories,

                "subcategories":
                    subcategories,

                **global_context
            }
        )


    except Exception as e:

        print(
            "=========================================="
        )

        print(
            "❌ ERREUR PAGE MODIFICATION"
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


        request.session["message"] = (
            "❌ Impossible d'ouvrir la modification."
        )


        return RedirectResponse(
            "/mes-annonces",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# TRAITER LA MODIFICATION
# POST /annonce/modifier/{product_id}
# ============================================================

@router.post("/annonce/modifier/{product_id}")
async def modifier_annonce(

    request: Request,

    product_id: int,

    title: str = Form(...),

    description: str = Form(...),

    price: float = Form(...),

    city: str = Form(...),

    condition: str = Form(...),

    category_id: int = Form(...),

    subcategory_id: int = Form(...),

    delivery_available: str | None = Form(None),

    image: UploadFile = File(None)

):

    user_id = request.session.get(
        "user_id"
    )


    # --------------------------------------------------------
    # VÉRIFIER CONNEXION
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )


    db = SessionLocal()


    try:

        # ----------------------------------------------------
        # RÉCUPÉRER UNIQUEMENT SON PRODUIT ACTIF
        # ----------------------------------------------------

        product = (
            db.query(Product)
            .filter(

                Product.id == product_id,

                Product.user_id == user_id,

                Product.is_active == True
            )
            .first()
        )


        if not product:

            request.session["message"] = (
                "❌ Annonce introuvable ou accès refusé."
            )


            return RedirectResponse(
                "/mes-annonces",
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
        # VALIDATION TITRE
        # ----------------------------------------------------

        if not title:

            request.session["message"] = (
                "❌ Le titre est obligatoire."
            )


            return RedirectResponse(
                f"/annonce/modifier/{product_id}",
                status_code=303
            )


        # ----------------------------------------------------
        # VALIDATION PRIX
        # ----------------------------------------------------

        if price < 0:

            request.session["message"] = (
                "❌ Le prix ne peut pas être négatif."
            )


            return RedirectResponse(
                f"/annonce/modifier/{product_id}",
                status_code=303
            )


        # ----------------------------------------------------
        # CATÉGORIE + SOUS-CATÉGORIE
        # ----------------------------------------------------

        category, subcategory = (
            validate_category_and_subcategory(
                db,
                category_id,
                subcategory_id
            )
        )


        if not category or not subcategory:

            request.session["message"] = (
                "❌ Catégorie ou sous-catégorie invalide."
            )


            return RedirectResponse(
                f"/annonce/modifier/{product_id}",
                status_code=303
            )


        # ----------------------------------------------------
        # LIVRAISON
        # ----------------------------------------------------

        delivery_available_bool = parse_delivery(
            delivery_available
        )


        print(
            "=========================================="
        )

        print(
            "📦 MODIFICATION PRODUIT"
        )

        print(
            "ID :",
            product.id
        )

        print(
            "🏪 BOUTIQUE ID AVANT SAUVEGARDE :",
            product.boutique_id
        )

        print(
            "📦 DELIVERY REÇU :",
            repr(delivery_available)
        )

        print(
            "📦 DELIVERY FINAL :",
            delivery_available_bool
        )

        print(
            "=========================================="
        )


        # ----------------------------------------------------
        # MODIFIER INFORMATIONS
        #
        # IMPORTANT :
        # boutique_id N'EST PAS MODIFIÉ.
        #
        # Le produit conserve donc sa boutique actuelle.
        # ----------------------------------------------------

        product.title = title

        product.description = description

        product.price = price

        product.city = city

        product.condition = condition

        product.category_id = category_id

        product.subcategory_id = subcategory_id

        product.delivery_available = (
            delivery_available_bool
        )


        # ----------------------------------------------------
        # MODIFIER IMAGE SI NOUVELLE IMAGE
        # ----------------------------------------------------

        if image and image.filename:

            new_image = await save_product_image(
                image
            )


            if new_image:

                product.image = new_image

                print(
                    "[OK] NOUVELLE IMAGE ENREGISTREE"
                )

            else:

                print(
                    "[ERREUR] Nouvelle image non enregistrée."
                )


        # ----------------------------------------------------
        # BOUTIQUE ID AVANT SAUVEGARDE
        # ----------------------------------------------------

        print(
            "🏪 BOUTIQUE ID AVANT COMMIT :",
            product.boutique_id
        )


        # ----------------------------------------------------
        # SAUVEGARDER
        # ----------------------------------------------------

        db.commit()

        db.refresh(product)


        # ----------------------------------------------------
        # LOG APRÈS SAUVEGARDE
        # ----------------------------------------------------

        print(
            "=========================================="
        )

        print(
            "[OK] ANNONCE MODIFIÉE"
        )

        print(
            "ID :",
            product.id
        )

        print(
            "TITRE :",
            product.title
        )

        print(
            "IMAGE :",
            product.image
        )

        print(
            "LIVRAISON :",
            product.delivery_available
        )

        print(
            "🏪 BOUTIQUE ID APRÈS SAUVEGARDE :",
            product.boutique_id
        )

        print(
            "=========================================="
        )


        request.session["message"] = (
            f"[OK] Annonce « {product.title} » "
            "modifiée avec succès."
        )


        # ----------------------------------------------------
        # RETOUR SELON L'APPARTENANCE DU PRODUIT
        #
        # Produit dans une boutique :
        # -> /ma-boutique
        #
        # Produit indépendant :
        # -> /mes-annonces
        # ----------------------------------------------------

        if product.boutique_id is not None:

            print(
                "🏪 REDIRECTION : MA BOUTIQUE"
            )

            return RedirectResponse(
                "/ma-boutique",
                status_code=303
            )


        print(
            "📢 REDIRECTION : MES ANNONCES"
        )

        return RedirectResponse(
            "/mes-annonces",
            status_code=303
        )


    except Exception as e:

        db.rollback()


        print(
            "=========================================="
        )

        print(
            "❌ ERREUR MODIFICATION ANNONCE"
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


        request.session["message"] = (
            "❌ Impossible de modifier cette annonce."
        )


        return RedirectResponse(
            f"/annonce/modifier/{product_id}",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# SUPPRIMER UNE ANNONCE
#
# IMPORTANT :
#
# On ne supprime PAS physiquement le produit
# s'il est lié à une commande.
#
# On utilise :
#
# is_active = False
#
# afin de conserver les historiques.
# ============================================================

@router.post("/annonce/supprimer/{product_id}")
async def supprimer_annonce(
    request: Request,
    product_id: int
):

    user_id = request.session.get(
        "user_id"
    )


    # --------------------------------------------------------
    # VÉRIFIER CONNEXION
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )


    db = SessionLocal()


    try:

        # ----------------------------------------------------
        # RÉCUPÉRER UNIQUEMENT SON PRODUIT ACTIF
        # ----------------------------------------------------

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id,
                Product.user_id == user_id,
                Product.is_active == True
            )
            .first()
        )


        # ----------------------------------------------------
        # PRODUIT INTROUVABLE
        # ----------------------------------------------------

        if not product:

            request.session["message"] = (
                "❌ Annonce introuvable ou déjà supprimée."
            )

            return RedirectResponse(
                "/ma-boutique",
                status_code=303
            )


        # ----------------------------------------------------
        # CONSERVER LE TITRE
        # ----------------------------------------------------

        product_title = product.title


        # ----------------------------------------------------
        # VÉRIFIER SI LE PRODUIT EST PRÉSENT
        # DANS UNE COMMANDE
        # ----------------------------------------------------

        order_item_exists = (
            db.query(OrderItem)
            .filter(
                OrderItem.product_id == product.id
            )
            .first()
        )


        # ----------------------------------------------------
        # SI LE PRODUIT EST LIÉ À UNE COMMANDE
        # ----------------------------------------------------

        if order_item_exists:

            product.is_active = False

            db.commit()


            print(
                "=========================================="
            )

            print(
                "PRODUIT DÉSACTIVÉ - HISTORIQUE CONSERVÉ"
            )

            print(
                "ID :",
                product.id
            )

            print(
                "TITRE :",
                product_title
            )

            print(
                "UTILISATEUR :",
                user_id
            )

            print(
                "IS_ACTIVE :",
                product.is_active
            )

            print(
                "=========================================="
            )


            request.session["message"] = (
                f"✅ Annonce « {product_title} » "
                "supprimée avec succès."
            )


        # ----------------------------------------------------
        # SI LE PRODUIT N'A JAMAIS ÉTÉ COMMANDÉ
        # ----------------------------------------------------

        else:

            db.delete(product)

            db.commit()


            print(
                "=========================================="
            )

            print(
                "PRODUIT SUPPRIMÉ DÉFINITIVEMENT"
            )

            print(
                "ID :",
                product.id
            )

            print(
                "TITRE :",
                product_title
            )

            print(
                "UTILISATEUR :",
                user_id
            )

            print(
                "=========================================="
            )


            request.session["message"] = (
                f"✅ Annonce « {product_title} » "
                "supprimée avec succès."
            )


        # ----------------------------------------------------
        # RETOUR MA BOUTIQUE
        # ----------------------------------------------------

        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )


    except Exception as e:

        db.rollback()


        print(
            "❌ ERREUR SUPPRESSION PRODUIT :",
            str(e)
        )

        traceback.print_exc()


        request.session["message"] = (
            "❌ Une erreur est survenue lors "
            "de la suppression de l'annonce."
        )


        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# COMMANDES DU VENDEUR
# ============================================================

@router.get("/mes-commandes-vendeur")
async def mes_commandes_vendeur(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )


    # --------------------------------------------------------
    # VÉRIFIER CONNEXION
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )


    db = SessionLocal()


    try:

        # ----------------------------------------------------
        # RÉCUPÉRER LES ARTICLES APPARTENANT AU VENDEUR
        # ----------------------------------------------------

        order_items = (
            db.query(OrderItem)
            .join(
                Product,
                OrderItem.product_id == Product.id
            )
            .filter(
                Product.user_id == user_id
            )
            .order_by(
                OrderItem.order_id.desc()
            )
            .all()
        )


        # ----------------------------------------------------
        # REGROUPER LES ARTICLES PAR COMMANDE
        # ----------------------------------------------------

        commandes = {}


        for item in order_items:

            order = item.order


            if not order:

                continue


            if order.id not in commandes:

                commandes[order.id] = {
                    "order": order,
                    "items": [],
                    "total_vendeur": 0
                }


            commandes[order.id]["items"].append(
                item
            )


            commandes[order.id]["total_vendeur"] += (
                item.subtotal or 0
            )


        # ----------------------------------------------------
        # TRANSFORMER EN LISTE
        # ----------------------------------------------------

        commandes = list(
            commandes.values()
        )


        # ----------------------------------------------------
        # CONTEXTE GLOBAL
        # ----------------------------------------------------

        global_context = get_global_context(
            request,
            db
        )


        # ----------------------------------------------------
        # AFFICHAGE
        # ----------------------------------------------------

        return templates.TemplateResponse(

            request=request,

            name="mes_commandes_vendeur.html",

            context={

                "commandes":
                    commandes,

                **global_context
            }
        )


    except Exception as e:

        print(
            "❌ ERREUR COMMANDES VENDEUR :",
            str(e)
        )

        traceback.print_exc()


        request.session["message"] = (
            "❌ Impossible de récupérer vos commandes."
        )


        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )


    finally:

        db.close()

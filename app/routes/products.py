from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal

from app.models.product import Product
from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.boutique import Boutique
from app.models.order_item import OrderItem

from app.translations.fr import TRANSLATIONS as FR
from app.translations.ar import TRANSLATIONS as AR

from supabase import create_client
from dotenv import load_dotenv

import os
from uuid import uuid4


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# SUPABASE STORAGE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SUPABASE_BUCKET = "product-images"

supabase = None


if SUPABASE_URL and SUPABASE_KEY:

    try:

        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        print("✅ Client Supabase initialisé")
        print(
            "✅ Bucket images produits :",
            SUPABASE_BUCKET
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
# TYPES D'IMAGES AUTORISÉS
# ============================================================

ALLOWED_IMAGE_TYPES = {

    "image/jpeg": ".jpg",

    "image/png": ".png",

    "image/webp": ".webp"
}


# ============================================================
# UPLOAD IMAGE PRODUIT SUR SUPABASE
# ============================================================

async def upload_product_image(
    image: UploadFile
):

    if not image or not image.filename:

        print(
            "ℹ️ Aucun fichier image fourni."
        )

        return None


    if not supabase:

        print(
            "❌ Supabase n'est pas configuré."
        )

        return None


    extension = ALLOWED_IMAGE_TYPES.get(
        image.content_type
    )

    if not extension:

        print(
            "❌ Type d'image non autorisé :",
            image.content_type
        )

        return None


    content = await image.read()

    if not content:

        print(
            "❌ Image vide."
        )

        return None


    filename = (
        f"product_"
        f"{uuid4().hex}"
        f"{extension}"
    )


    try:

        (
            supabase
            .storage
            .from_(SUPABASE_BUCKET)
            .upload(
                path=filename,
                file=content,
                file_options={
                    "content-type": image.content_type,
                    "cache-control": "3600",
                    "upsert": "false"
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
            SUPABASE_BUCKET
        )

        print(
            "FICHIER :",
            filename
        )

        print(
            "=========================================="
        )


    except Exception as e:

        print(
            "=========================================="
        )

        print(
            "❌ ERREUR UPLOAD IMAGE PRODUIT"
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
            "✅ URL SUPABASE :",
            public_url
        )

        return public_url


    except Exception as e:

        print(
            "❌ ERREUR RÉCUPÉRATION URL :",
            repr(e)
        )

        return None


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


    # --------------------------------------------------------
    # LANGUE
    # --------------------------------------------------------

    lang = request.query_params.get(
        "lang",
        "fr"
    )

    if lang not in ["fr", "ar"]:

        lang = "fr"


    translations = (
        FR
        if lang == "fr"
        else AR
    )


    return {

        "user_name":
            user_name,

        "user_id":
            user_id,

        "panier_count":
            len(panier),

        "lang":
            lang,

        "t":
            translations,

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
# PUBLIER DEPUIS L'ACCUEIL
# GET /publier
#
# ANNONCE SIMPLE UNIQUEMENT
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
# ANNONCE SIMPLE
# boutique_id = None
# ============================================================

@router.post("/publier")
async def publish_product(

    request: Request,

    title: str = Form(...),

    title_ar: str = Form(""),

    description: str = Form(...),

    description_ar: str = Form(""),

    price: float = Form(...),

    city: str = Form(...),

    city_ar: str = Form(""),

    condition: str = Form(...),

    condition_ar: str = Form(""),

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

        title = title.strip()

        title_ar = title_ar.strip()

        description = description.strip()

        description_ar = description_ar.strip()

        city = city.strip()

        city_ar = city_ar.strip()

        condition = condition.strip()

        condition_ar = condition_ar.strip()


        category = (
            db.query(Category)
            .filter(
                Category.id == category_id
            )
            .first()
        )

        if not category:

            return RedirectResponse(
                "/publier",
                status_code=303
            )


        subcategory = (
            db.query(SubCategory)
            .filter(
                SubCategory.id == subcategory_id
            )
            .first()
        )

        if not subcategory:

            return RedirectResponse(
                "/publier",
                status_code=303
            )


        if (
            subcategory.category_id
            != category_id
        ):

            print(
                "Sous-catégorie incompatible."
            )

            return RedirectResponse(
                "/publier",
                status_code=303
            )


        image_path = await upload_product_image(
            image
        )


        product = Product(

            title=title,

            title_ar=title_ar or None,

            description=description,

            description_ar=description_ar or None,

            price=price,

            city=city,

            city_ar=city_ar or None,

            condition=condition,

            condition_ar=condition_ar or None,

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
            "✅ ANNONCE SIMPLE PUBLIÉE"
        )

        print(
            "ID :",
            product.id
        )

        print(
            "TITRE FR :",
            product.title
        )

        print(
            "TITRE AR :",
            product.title_ar
        )

        print(
            "BOUTIQUE ID :",
            product.boutique_id
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
            "=========================================="
        )


        return RedirectResponse(
            "/mes-annonces",
            status_code=303
        )


    except Exception as e:

        db.rollback()

        print(
            "ERREUR PUBLICATION :",
            repr(e)
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
# ============================================================

@router.post("/ma-boutique/publier")
async def publish_boutique_product(

    request: Request,

    title: str = Form(...),

    title_ar: str = Form(""),

    description: str = Form(...),

    description_ar: str = Form(""),

    price: float = Form(...),

    city: str = Form(...),

    city_ar: str = Form(""),

    condition: str = Form(...),

    condition_ar: str = Form(""),

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


        title = title.strip()

        title_ar = title_ar.strip()

        description = description.strip()

        description_ar = description_ar.strip()

        city = city.strip()

        city_ar = city_ar.strip()

        condition = condition.strip()

        condition_ar = condition_ar.strip()


        category = (
            db.query(Category)
            .filter(
                Category.id == category_id
            )
            .first()
        )

        if not category:

            return RedirectResponse(
                "/ma-boutique/publier",
                status_code=303
            )


        subcategory = (
            db.query(SubCategory)
            .filter(
                SubCategory.id == subcategory_id
            )
            .first()
        )

        if not subcategory:

            return RedirectResponse(
                "/ma-boutique/publier",
                status_code=303
            )


        if (
            subcategory.category_id
            != category_id
        ):

            print(
                "Sous-catégorie incompatible."
            )

            return RedirectResponse(
                "/ma-boutique/publier",
                status_code=303
            )


        image_path = await upload_product_image(
            image
        )


        product = Product(

            title=title,

            title_ar=title_ar or None,

            description=description,

            description_ar=description_ar or None,

            price=price,

            city=city,

            city_ar=city_ar or None,

            condition=condition,

            condition_ar=condition_ar or None,

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
            "TITRE FR :",
            product.title
        )

        print(
            "TITRE AR :",
            product.title_ar
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
            "=========================================="
        )


        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )


    except Exception as e:

        db.rollback()

        print(
            "ERREUR PUBLICATION BOUTIQUE :",
            repr(e)
        )

        return RedirectResponse(
            "/ma-boutique/publier",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# MES ANNONCES
# GET /mes-annonces
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

                Product.boutique_id.is_(None),

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

                **global_context
            }
        )


    except Exception as e:

        print(
            "ERREUR GET /mes-annonces :",
            repr(e)
        )

        return RedirectResponse(
            "/",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# DÉTAIL DU PRODUIT
# GET /produit/{product_id}
# ============================================================

@router.get("/produit/{product_id}")
async def product_detail(

    request: Request,

    product_id: int

):

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(

                Product.id == product_id,

                Product.is_active == True

            )
            .first()
        )


        if not product:

            lang = request.query_params.get(
                "lang",
                "fr"
            )

            if lang not in ["fr", "ar"]:
                lang = "fr"

            return RedirectResponse(
                f"/?lang={lang}",
                status_code=303
            )


        product.views += 1

        db.commit()

        db.refresh(product)


        global_context = get_global_context(
            request,
            db
        )


        return templates.TemplateResponse(

            request=request,

            name="product_detail.html",

            context={

                "product":
                    product,

                **global_context
            }
        )


    except Exception as e:

        db.rollback()

        print(
            "ERREUR DÉTAIL PRODUIT :",
            repr(e)
        )

        lang = request.query_params.get(
            "lang",
            "fr"
        )

        if lang not in ["fr", "ar"]:
            lang = "fr"

        return RedirectResponse(
            f"/?lang={lang}",
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
                Product.user_id == user_id
            )
            .first()
        )


        if not product:

            print(
                "❌ Produit introuvable ou non autorisé :",
                product_id
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

            name="modifier.html",

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
            "ERREUR GET MODIFICATION ANNONCE :",
            repr(e)
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

    title_ar: str = Form(""),

    description: str = Form(...),

    description_ar: str = Form(""),

    price: float = Form(...),

    city: str = Form(...),

    city_ar: str = Form(""),

    condition: str = Form(...),

    condition_ar: str = Form(""),

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

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id,
                Product.user_id == user_id
            )
            .first()
        )


        if not product:

            return RedirectResponse(
                "/mes-annonces",
                status_code=303
            )


        title = title.strip()

        title_ar = title_ar.strip()

        description = description.strip()

        description_ar = description_ar.strip()

        city = city.strip()

        city_ar = city_ar.strip()

        condition = condition.strip()

        condition_ar = condition_ar.strip()


        category = (
            db.query(Category)
            .filter(
                Category.id == category_id
            )
            .first()
        )


        if not category:

            return RedirectResponse(
                f"/annonce/modifier/{product_id}",
                status_code=303
            )


        subcategory = (
            db.query(SubCategory)
            .filter(
                SubCategory.id == subcategory_id
            )
            .first()
        )


        if not subcategory:

            return RedirectResponse(
                f"/annonce/modifier/{product_id}",
                status_code=303
            )


        if (
            subcategory.category_id
            != category_id
        ):

            print(
                "Sous-catégorie incompatible."
            )

            return RedirectResponse(
                f"/annonce/modifier/{product_id}",
                status_code=303
            )


        # ----------------------------------------------------
        # MISE À JOUR DES INFORMATIONS
        # ----------------------------------------------------

        product.title = title

        product.title_ar = (
            title_ar or None
        )

        product.description = description

        product.description_ar = (
            description_ar or None
        )

        product.price = price

        product.city = city

        product.city_ar = (
            city_ar or None
        )

        product.condition = condition

        product.condition_ar = (
            condition_ar or None
        )

        product.category_id = category_id

        product.subcategory_id = subcategory_id


        # ----------------------------------------------------
        # NOUVELLE IMAGE
        # ----------------------------------------------------

        if image and image.filename:

            new_image_url = await upload_product_image(
                image
            )

            if new_image_url:

                product.image = new_image_url

                print(
                    "✅ Nouvelle image enregistrée."
                )

            else:

                print(
                    "⚠️ Nouvelle image invalide."
                    " Ancienne image conservée."
                )


        db.commit()

        db.refresh(product)


        print(
            "=========================================="
        )

        print(
            "✅ ANNONCE MODIFIÉE"
        )

        print(
            "ID :",
            product.id
        )

        print(
            "TITRE FR :",
            product.title
        )

        print(
            "TITRE AR :",
            product.title_ar
        )

        print(
            "BOUTIQUE ID :",
            product.boutique_id
        )

        print(
            "IMAGE :",
            product.image
        )

        print(
            "=========================================="
        )


        if product.boutique_id is None:

            return RedirectResponse(
                "/mes-annonces",
                status_code=303
            )

        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )


    except Exception as e:

        db.rollback()

        print(
            "ERREUR MODIFICATION ANNONCE :",
            repr(e)
        )

        return RedirectResponse(
            f"/annonce/modifier/{product_id}",
            status_code=303
        )


    finally:

        db.close()


# ============================================================
# SUPPRIMER UNE ANNONCE
# POST /annonce/supprimer/{product_id}
# ============================================================

@router.post("/annonce/supprimer/{product_id}")
async def supprimer_annonce(

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
                Product.user_id == user_id
            )
            .first()
        )


        if not product:

            print(
                "❌ Produit introuvable ou non autorisé :",
                product_id
            )

            return RedirectResponse(
                "/mes-annonces",
                status_code=303
            )


        is_simple_announcement = (
            product.boutique_id is None
        )


        order_item = (
            db.query(OrderItem)
            .filter(
                OrderItem.product_id == product.id
            )
            .first()
        )


        if order_item:

            product.is_active = False

            db.commit()


            print(
                "=========================================="
            )

            print(
                "⚠️ PRODUIT DÉSACTIVÉ"
            )

            print(
                "Le produit existe dans une commande."
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
                "BOUTIQUE ID :",
                product.boutique_id
            )

            print(
                "=========================================="
            )


        else:

            print(
                "=========================================="
            )

            print(
                "🗑️ SUPPRESSION ANNONCE"
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
                "BOUTIQUE ID :",
                product.boutique_id
            )

            print(
                "=========================================="
            )


            db.delete(product)

            db.commit()


        if is_simple_announcement:

            return RedirectResponse(
                "/mes-annonces",
                status_code=303
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
            "❌ ERREUR SUPPRESSION ANNONCE"
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


        try:

            product = (
                db.query(Product)
                .filter(
                    Product.id == product_id,
                    Product.user_id == user_id
                )
                .first()
            )

            if product and product.boutique_id is not None:

                return RedirectResponse(
                    "/ma-boutique",
                    status_code=303
                )

        except Exception:

            pass


        return RedirectResponse(
            "/mes-annonces",
            status_code=303
        )


    finally:

        db.close()

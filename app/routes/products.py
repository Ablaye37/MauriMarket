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
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

BUCKET_NAME = "product-images"


supabase = None

if SUPABASE_URL and SUPABASE_KEY:

    try:

        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        print(
            "âœ… Client Supabase initialisÃ©"
        )

        print(
            "âœ… Bucket images produits :",
            BUCKET_NAME
        )

    except Exception as e:

        print(
            "âŒ ERREUR INITIALISATION SUPABASE :",
            repr(e)
        )

else:

    print(
        "âŒ SUPABASE_URL ou SUPABASE_KEY manquant."
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
# CATÃ‰GORIES
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
# SOUS-CATÃ‰GORIES
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
# AUCUNE IMAGE PRODUIT N'EST SAUVEGARDÃ‰E
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
            "â„¹ï¸ Aucun fichier image fourni."
        )

        return None


    # --------------------------------------------------------
    # VÃ‰RIFIER SUPABASE
    # --------------------------------------------------------

    if not supabase:

        print(
            "âŒ Supabase n'est pas configurÃ©."
        )

        return None


    # --------------------------------------------------------
    # TYPES AUTORISÃ‰S
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
            "âŒ Type d'image non autorisÃ© :",
            image.content_type
        )

        return None


    # --------------------------------------------------------
    # LIRE IMAGE
    # --------------------------------------------------------

    content = await image.read()


    if not content:

        print(
            "âŒ Image vide."
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
            "âœ… IMAGE ENVOYÃ‰E SUR SUPABASE"
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
            "âŒ ERREUR UPLOAD SUPABASE"
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
    # RÃ‰CUPÃ‰RER URL PUBLIQUE
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
            "âœ… URL IMAGE SUPABASE :",
            public_url
        )


        return public_url


    except Exception as e:

        print(
            "âŒ ERREUR URL SUPABASE :",
            repr(e)
        )

        return None


# ============================================================
# VÃ‰RIFIER CATÃ‰GORIE + SOUS-CATÃ‰GORIE
# ============================================================

def validate_category_and_subcategory(
    db,
    category_id: int,
    subcategory_id: int
):

    # --------------------------------------------------------
    # CATÃ‰GORIE
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
    # SOUS-CATÃ‰GORIE
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
    # VÃ‰RIFIER RELATION
    # --------------------------------------------------------

    if (
        subcategory.category_id
        != category_id
    ):

        print(
            "âŒ Sous-catÃ©gorie incompatible."
        )

        print(
            "CatÃ©gorie sÃ©lectionnÃ©e :",
            category_id
        )

        print(
            "CatÃ©gorie de la sous-catÃ©gorie :",
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
# Produit indÃ©pendant
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
        # VÃ‰RIFIER CATÃ‰GORIE
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
        # CRÃ‰ER PRODUIT INDÃ‰PENDANT
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
            "âœ… PRODUIT PUBLIÃ‰ INDÃ‰PENDANT"
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
            "CATÃ‰GORIE ID :",
            product.category_id
        )

        print(
            "SOUS-CATÃ‰GORIE ID :",
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
            "âŒ ERREUR PUBLICATION"
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
# Produit appartenant Ã  la boutique du vendeur
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
        # RÃ‰CUPÃ‰RER LA BOUTIQUE DU VENDEUR
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
        # VÃ‰RIFIER CATÃ‰GORIE
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
        # CRÃ‰ER PRODUIT DANS LA BOUTIQUE
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
            "âœ… PRODUIT PUBLIÃ‰ DANS MA BOUTIQUE"
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
            "CATÃ‰GORIE ID :",
            product.category_id
        )

        print(
            "SOUS-CATÃ‰GORIE ID :",
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
            "âŒ ERREUR PUBLICATION BOUTIQUE"
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



# ============================================================
# MES ANNONCES
# ============================================================

@router.get("/mes-annonces")
async def mes_annonces(
    request: Request
):

    user_id = request.session.get("user_id")

    # --------------------------------------------------------
    # VÃ‰RIFIER CONNEXION
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # RÃ‰CUPÃ‰RER UNIQUEMENT LES PRODUITS DE L'UTILISATEUR
        # QUI NE SONT PAS DANS UNE BOUTIQUE
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # CONTEXTE
        # ----------------------------------------------------

        global_context = get_global_context(
            request,
            db
        )

        # ----------------------------------------------------
        # AFFICHER MES ANNONCES
        # ----------------------------------------------------

        return templates.TemplateResponse(

            request=request,

            name="mes_annonces.html",

            context={

                "products": products,

                "annonces": products,

                **global_context
            }
        )

    except Exception as e:

        print(
            "âŒ ERREUR /mes-annonces :",
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
# MODIFIER UNE ANNONCE
# ============================================================

@router.get("/annonce/modifier/{product_id}")
async def modifier_annonce_page(
    request: Request,
    product_id: int
):

    user_id = request.session.get("user_id")

    # --------------------------------------------------------
    # VÃ‰RIFIER CONNEXION
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # RÃ‰CUPÃ‰RER UNIQUEMENT SON PROPRE PRODUIT
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
                "âŒ Annonce introuvable ou accÃ¨s refusÃ©."
            )

            return RedirectResponse(
                "/ma-boutique",
                status_code=303
            )

        # ----------------------------------------------------
        # CATÃ‰GORIES
        # ----------------------------------------------------

        categories = get_categories(db)

        subcategories = get_subcategories(db)

        # ----------------------------------------------------
        # CONTEXTE GLOBAL
        # ----------------------------------------------------

        global_context = get_global_context(
            request,
            db
        )

        # ----------------------------------------------------
        # PAGE DE MODIFICATION
        # ----------------------------------------------------

        return templates.TemplateResponse(

            request=request,

            name="modifier_produit.html",

            context={

                "product": product,

                "categories": categories,

                "subcategories": subcategories,

                **global_context
            }
        )

    except Exception as e:

        print(
            "âŒ ERREUR PAGE MODIFICATION :",
            repr(e)
        )

        traceback.print_exc()

        request.session["message"] = (
            "âŒ Impossible d'ouvrir la modification."
        )

        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )

    finally:

        db.close()


# ============================================================
# TRAITER LA MODIFICATION
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

    image: UploadFile = File(None)
):

    user_id = request.session.get("user_id")

    # --------------------------------------------------------
    # VÃ‰RIFIER CONNEXION
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # RÃ‰CUPÃ‰RER UNIQUEMENT SON PROPRE PRODUIT
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
                "âŒ Annonce introuvable ou accÃ¨s refusÃ©."
            )

            return RedirectResponse(
                "/ma-boutique",
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
        # VÃ‰RIFIER TITRE
        # ----------------------------------------------------

        if not title:

            request.session["message"] = (
                "âŒ Le titre est obligatoire."
            )

            return RedirectResponse(
                f"/annonce/modifier/{product_id}",
                status_code=303
            )

        # ----------------------------------------------------
        # VÃ‰RIFIER PRIX
        # ----------------------------------------------------

        if price < 0:

            request.session["message"] = (
                "âŒ Le prix ne peut pas Ãªtre nÃ©gatif."
            )

            return RedirectResponse(
                f"/annonce/modifier/{product_id}",
                status_code=303
            )

        # ----------------------------------------------------
        # VÃ‰RIFIER CATÃ‰GORIE + SOUS-CATÃ‰GORIE
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
                "âŒ CatÃ©gorie ou sous-catÃ©gorie invalide."
            )

            return RedirectResponse(
                f"/annonce/modifier/{product_id}",
                status_code=303
            )

        # ----------------------------------------------------
        # MODIFIER LES INFORMATIONS
        # ----------------------------------------------------

        product.title = title

        product.description = description

        product.price = price

        product.city = city

        product.condition = condition

        product.category_id = category_id

        product.subcategory_id = subcategory_id

        # ----------------------------------------------------
        # MODIFIER L'IMAGE SI UNE NOUVELLE IMAGE EST FOURNIE
        # ----------------------------------------------------

        if image and image.filename:

            new_image = await save_product_image(
                image
            )

            if new_image:

                product.image = new_image

        # ----------------------------------------------------
        # SAUVEGARDER
        # ----------------------------------------------------

        db.commit()

        request.session["message"] = (
            f"âœ… Annonce Â« {product.title} Â» "
            "modifiÃ©e avec succÃ¨s."
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
            "âŒ ERREUR MODIFICATION ANNONCE :",
            repr(e)
        )

        traceback.print_exc()

        request.session["message"] = (
            "âŒ Impossible de modifier cette annonce."
        )

        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )

    finally:

        db.close()


# ============================================================
# SUPPRIMER UNE ANNONCE
#
# IMPORTANT :
# On ne fait PAS db.delete(product).
#
# On met simplement :
#
# is_active = False
#
# Cela permet de conserver les commandes historiques.
# ============================================================

@router.post("/annonce/supprimer/{product_id}")
async def supprimer_annonce(

    request: Request,

    product_id: int
):

    user_id = request.session.get("user_id")

    # --------------------------------------------------------
    # VÃ‰RIFIER CONNEXION
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # RÃ‰CUPÃ‰RER UNIQUEMENT SON PROPRE PRODUIT
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
                "âŒ Annonce introuvable ou accÃ¨s refusÃ©."
            )

            return RedirectResponse(
                "/ma-boutique",
                status_code=303
            )

        # ----------------------------------------------------
        # NOM POUR MESSAGE
        # ----------------------------------------------------

        product_title = product.title

        # ----------------------------------------------------
        # DÃ‰SACTIVER AU LIEU DE SUPPRIMER
        # ----------------------------------------------------

        product.is_active = False

        db.commit()

        # ----------------------------------------------------
        # MESSAGE
        # ----------------------------------------------------

        request.session["message"] = (
            f"ðŸ—‘ï¸ Annonce Â« {product_title} Â» "
            "supprimÃ©e avec succÃ¨s."
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
            "âŒ ERREUR SUPPRESSION ANNONCE :",
            repr(e)
        )

        traceback.print_exc()

        request.session["message"] = (
            "âŒ Impossible de supprimer cette annonce."
        )

        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )

    finally:

        db.close()

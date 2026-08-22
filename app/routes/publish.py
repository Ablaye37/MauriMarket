from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal

from app.models.product import Product
from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.boutique import Boutique

import os
import uuid


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# CONFIGURATION
# ============================================================

UPLOAD_DIR = "app/static/uploads/products"


# ============================================================
# CONTEXTE GLOBAL
# ============================================================

def get_global_context(request: Request, db):

    user_id = request.session.get("user_id")
    user_name = request.session.get("user_name")

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
        "has_boutique": boutique is not None,
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
# SAUVEGARDER IMAGE
# ============================================================

async def save_product_image(
    image: UploadFile
):

    if not image or not image.filename:
        return None

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp"
    }

    extension = allowed_types.get(
        image.content_type
    )

    if not extension:
        return None

    os.makedirs(
        UPLOAD_DIR,
        exist_ok=True
    )

    filename = (
        f"product_"
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    content = await image.read()

    if not content:
        return None

    with open(
        file_path,
        "wb"
    ) as file:

        file.write(content)

    return (
        f"/static/uploads/products/"
        f"{filename}"
    )


# ============================================================
# PUBLIER DEPUIS L'ACCUEIL
# GET /publier
#
# IMPORTANT :
# Une annonce publiée ici est une annonce INDÉPENDANTE.
#
# Elle ne doit JAMAIS être automatiquement rattachée
# à la boutique de l'utilisateur.
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

        categories = get_categories(db)

        subcategories = get_subcategories(db)

        global_context = get_global_context(
            request,
            db
        )

        return templates.TemplateResponse(
            request=request,
            name="publier.html",
            context={
                "categories": categories,
                "subcategories": subcategories,
                "is_boutique_publish": False,
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

        categories = get_categories(db)

        subcategories = get_subcategories(db)

        global_context = get_global_context(
            request,
            db
        )

        return templates.TemplateResponse(
            request=request,
            name="publier.html",
            context={
                "categories": categories,
                "subcategories": subcategories,
                "boutique": boutique,
                "is_boutique_publish": True,
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
# IMPORTANT :
# ICI boutique_id DOIT ÊTRE None.
#
# Même si l'utilisateur possède une boutique,
# cette annonce reste indépendante.
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

        title = title.strip()
        description = description.strip()
        city = city.strip()
        condition = condition.strip()

        # ----------------------------------------------------
        # VÉRIFIER CATÉGORIE
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # VÉRIFIER SOUS-CATÉGORIE
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # VÉRIFIER RELATION CATÉGORIE
        # ----------------------------------------------------

        if subcategory.category_id != category_id:

            print(
                "Sous-catégorie incompatible."
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
        # CRÉER PRODUIT INDÉPENDANT
        #
        # TRÈS IMPORTANT :
        #
        # boutique_id = None
        #
        # On NE cherche PAS la boutique de l'utilisateur.
        # Même s'il possède une boutique, cette annonce
        # publiée depuis /publier reste indépendante.
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
            "PRODUIT PUBLIÉ INDÉPENDANT"
        )

        print(
            "ID :",
            product.id
        )

        print(
            "BOUTIQUE ID :",
            product.boutique_id
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
            "/",
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
#
# ICI SEULEMENT :
#
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

        description = (
            description.strip()
        )

        city = city.strip()

        condition = (
            condition.strip()
        )

        # ----------------------------------------------------
        # VÉRIFIER CATÉGORIE
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # VÉRIFIER SOUS-CATÉGORIE
        # ----------------------------------------------------

        subcategory = (
            db.query(SubCategory)
            .filter(
                SubCategory.id
                == subcategory_id
            )
            .first()
        )

        if not subcategory:

            return RedirectResponse(
                "/ma-boutique/publier",
                status_code=303
            )

        # ----------------------------------------------------
        # VÉRIFIER RELATION
        # ----------------------------------------------------

        if (
            subcategory.category_id
            != category_id
        ):

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
            "PRODUIT PUBLIÉ DANS MA BOUTIQUE"
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
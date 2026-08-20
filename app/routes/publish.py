import os
import uuid

from dotenv import load_dotenv
from supabase import create_client

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.product import Product
from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.boutique import Boutique
from app.models.boutique_request import BoutiqueRequest


# =====================================================
# SUPABASE
# =====================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

BUCKET_NAME = "product-images"


# =====================================================
# ROUTER
# =====================================================

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =====================================================
# FONCTION : CATÉGORIES
# =====================================================

def recuperer_categories(db):

    categories = (
        db.query(Category)
        .order_by(Category.id)
        .all()
    )

    subcategories = (
        db.query(SubCategory)
        .order_by(SubCategory.id)
        .all()
    )

    return categories, subcategories


# =====================================================
# PUBLICATION ANNONCE CLASSIQUE
# =====================================================

@router.get("/publier")
async def afficher_publier(request: Request):

    user_id = request.session.get("user_id")

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        categories, subcategories = recuperer_categories(db)

        return templates.TemplateResponse(
            request=request,
            name="publier.html",
            context={
                "categories": categories,
                "subcategories": subcategories
            }
        )

    finally:

        db.close()


# =====================================================
# CRÉER UNE ANNONCE CLASSIQUE
# =====================================================

@router.post("/publier")
async def creer_annonce(
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

    user_id = request.session.get("user_id")

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # =================================================
        # IMAGE
        # =================================================

        image_url = None

        if image and image.filename:

            extension = os.path.splitext(
                image.filename
            )[1].lower()

            file_name = f"{uuid.uuid4()}{extension}"

            file_data = await image.read()

            supabase.storage.from_(
                BUCKET_NAME
            ).upload(
                file_name,
                file_data,
                {
                    "content-type": (
                        image.content_type
                        or "application/octet-stream"
                    )
                }
            )

            image_url = (
                supabase.storage.from_(
                    BUCKET_NAME
                ).get_public_url(
                    file_name
                )
            )

        # =================================================
        # ANNONCE CLASSIQUE
        # =================================================

        produit = Product(
            title=title,
            description=description,
            price=price,
            city=city,
            condition=condition,
            category_id=category_id,
            subcategory_id=subcategory_id,
            image=image_url,
            user_id=user_id,

            # Une annonce classique
            # n'appartient à aucune boutique
            boutique_id=None
        )

        db.add(produit)

        db.commit()

        return RedirectResponse(
            "/",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# PUBLIER DANS MA BOUTIQUE
# =====================================================

@router.get("/ma-boutique/publier")
async def afficher_publier_boutique(
    request: Request
):

    user_id = request.session.get("user_id")

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # =================================================
        # VÉRIFIER LA BOUTIQUE
        # =================================================

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

        # =================================================
        # BOUTIQUE ACCEPTÉE
        # =================================================

        if boutique:

            categories, subcategories = (
                recuperer_categories(db)
            )

        return templates.TemplateResponse(
        request=request,
        name="publier_produit_boutique.html",
        context={
        "categories": categories,
        "subcategories": subcategories,
        "boutique": boutique
    }
)

        # =================================================
        # PAS ENCORE DE BOUTIQUE
        # CHERCHER UNE DEMANDE
        # =================================================

        boutique_request = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.user_id == user_id
            )
            .order_by(
                BoutiqueRequest.id.desc()
            )
            .first()
        )

        # =================================================
        # DEMANDE EN ATTENTE
        # =================================================

        if (
            boutique_request
            and boutique_request.status == "pending"
        ):

            request.session["message"] = (
                "Votre demande de boutique est encore en attente "
                "de validation par l'administrateur."
            )

            return RedirectResponse(
                "/boutique/creer",
                status_code=303
            )

        # =================================================
        # DEMANDE REFUSÉE OU AUCUNE DEMANDE
        # =================================================

        return RedirectResponse(
            "/boutique/creer",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# CRÉER UN PRODUIT DANS MA BOUTIQUE
# =====================================================

@router.post("/ma-boutique/publier")
async def creer_produit_boutique(
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

    user_id = request.session.get("user_id")

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # =================================================
        # VÉRIFIER LA BOUTIQUE
        # =================================================

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

        # =================================================
        # SÉCURITÉ
        # =================================================

        if not boutique:

            request.session["message"] = (
                "Vous devez avoir une boutique approuvée "
                "pour publier dans une boutique."
            )

            return RedirectResponse(
                "/boutique/creer",
                status_code=303
            )

        # =================================================
        # IMAGE
        # =================================================

        image_url = None

        if image and image.filename:

            extension = os.path.splitext(
                image.filename
            )[1].lower()

            file_name = f"{uuid.uuid4()}{extension}"

            file_data = await image.read()

            supabase.storage.from_(
                BUCKET_NAME
            ).upload(
                file_name,
                file_data,
                {
                    "content-type": (
                        image.content_type
                        or "application/octet-stream"
                    )
                }
            )

            image_url = (
                supabase.storage.from_(
                    BUCKET_NAME
                ).get_public_url(
                    file_name
                )
            )

        # =================================================
        # PRODUIT DE LA BOUTIQUE
        # =================================================

        produit = Product(
            title=title,
            description=description,
            price=price,
            city=city,
            condition=condition,
            category_id=category_id,
            subcategory_id=subcategory_id,
            image=image_url,
            user_id=user_id,

            # IMPORTANT :
            # Le produit appartient à la boutique
            boutique_id=boutique.id
        )

        db.add(produit)

        db.commit()

        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )

    finally:

        db.close()
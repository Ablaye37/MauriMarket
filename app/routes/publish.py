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
# PAGE PUBLICATION
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

    categories = db.query(Category).all()
    subcategories = db.query(SubCategory).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="publier.html",
        context={
            "categories": categories,
            "subcategories": subcategories
        }
    )


# =====================================================
# CRÉATION PRODUIT
# =====================================================

@router.post("/publier")
async def creer_produit(
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


    # =================================================
    # IMAGE SUPABASE STORAGE
    # =================================================

    image_url = None

    if image and image.filename:

        # Extension du fichier
        extension = os.path.splitext(
            image.filename
        )[1].lower()

        # Nom unique
        file_name = (
            f"{uuid.uuid4()}{extension}"
        )

        # Lire l'image
        file_data = await image.read()

        # Envoyer vers Supabase Storage
        supabase.storage.from_(
            BUCKET_NAME
        ).upload(
            file_name,
            file_data,
            {
                "content-type": image.content_type or "application/octet-stream"
            }
        )

        # URL publique
        image_url = supabase.storage.from_(
            BUCKET_NAME
        ).get_public_url(
            file_name
        )


    # =================================================
    # BASE DE DONNÉES
    # =================================================

    db = SessionLocal()

    produit = Product(
        title=title,
        description=description,
        price=price,
        city=city,
        condition=condition,

        category_id=category_id,
        subcategory_id=subcategory_id,

        image=image_url,
        user_id=user_id
    )

    db.add(produit)

    db.commit()

    db.close()


    # =================================================
    # RETOUR ACCUEIL
    # =================================================

    return RedirectResponse(
        "/",
        status_code=303
    )
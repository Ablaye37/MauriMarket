from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.product import Product
from app.models.category import Category
from app.models.subcategory import SubCategory

import shutil
import os


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


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
    # IMAGE
    # =================================================

    image_name = None

    if image and image.filename:

        upload_dir = "app/static/uploads"

        os.makedirs(
            upload_dir,
            exist_ok=True
        )

        image_name = image.filename

        image_path = os.path.join(
            upload_dir,
            image_name
        )

        with open(
            image_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                image.file,
                buffer
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

        image=image_name,
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
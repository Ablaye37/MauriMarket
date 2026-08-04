from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.product import Product
from app.models.category import Category

import shutil
import os


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# Page publication
@router.get("/publier")
async def afficher_publier(request: Request):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)


    db = SessionLocal()

    categories = db.query(Category).all()

    db.close()


    return templates.TemplateResponse(
        request=request,
        name="publier.html",
        context={
            "categories": categories
        }
    )



# Création produit
@router.post("/publier")
async def creer_produit(
    request: Request,

    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    city: str = Form(...),
    condition: str = Form(...),
    category_id: int = Form(...),
    image: UploadFile = File(None)
):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)



    image_name = None


    if image and image.filename:

        os.makedirs(
            "app/static/uploads",
            exist_ok=True
        )


        image_name = image.filename


        with open(
            f"app/static/uploads/{image_name}",
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                image.file,
                buffer
            )



    db = SessionLocal()


    produit = Product(
        title=title,
        description=description,
        price=price,
        city=city,
        condition=condition,
        category_id=category_id,
        image=image_name,
        user_id=user_id
    )


    db.add(produit)

    db.commit()

    db.close()



    return RedirectResponse(
        "/",
        status_code=303
    )
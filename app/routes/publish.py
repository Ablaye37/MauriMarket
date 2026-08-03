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


<<<<<<< HEAD
# Page publication
@router.get("/publier")
async def afficher_publier(request: Request):

    # Vérifier connexion
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()

    categories = db.query(Category).all()

=======
@router.get("/publier")
async def afficher_publier(request: Request):
    db = SessionLocal()
    categories = db.query(Category).all()
>>>>>>> 99097da8588bad065ab8d809dfcaa1575e8a71b5
    db.close()

    return templates.TemplateResponse(
        request=request,
        name="publier.html",
<<<<<<< HEAD
        context={
            "categories": categories
        }
    )


# Création produit
@router.post("/publier")
async def creer_produit(
    request: Request,
=======
        context={"categories": categories}
    )


@router.post("/publier")
async def creer_produit(
>>>>>>> 99097da8588bad065ab8d809dfcaa1575e8a71b5
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    city: str = Form(...),
    condition: str = Form(...),
    category_id: int = Form(...),
    image: UploadFile = File(None)
):

<<<<<<< HEAD
    # Récupérer utilisateur connecté
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)


    image_name = None


    # Gestion image
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


=======
    image_name = None

    if image and image.filename:
        os.makedirs("app/static/uploads", exist_ok=True)

        image_name = image.filename

        with open(f"app/static/uploads/{image_name}", "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    db = SessionLocal()

>>>>>>> 99097da8588bad065ab8d809dfcaa1575e8a71b5
    produit = Product(
        title=title,
        description=description,
        price=price,
        city=city,
        condition=condition,
        category_id=category_id,
<<<<<<< HEAD
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
=======
        image=image_name
    )

    db.add(produit)
    db.commit()
    db.close()

    return RedirectResponse("/", status_code=303)

>>>>>>> 99097da8588bad065ab8d809dfcaa1575e8a71b5

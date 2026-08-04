from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import shutil
import os

from app.database.database import SessionLocal
from app.models.product import Product

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/publish")
def publish_page(request: Request):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="publish.html"
    )


@router.post("/publish")
def create_product(
    request: Request,

    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    city: str = Form(...),
    condition: str = Form(...),

    photo: UploadFile = File(None)
):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)


    filename = None


    if photo and photo.filename:

        filename = photo.filename

        upload_dir = "app/static/uploads"

        os.makedirs(
            upload_dir,
            exist_ok=True
        )

        photo_path = os.path.join(
            upload_dir,
            filename
        )

        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(
                photo.file,
                buffer
            )


    db = SessionLocal()


    product = Product(
        title=title,
        description=description,
        price=price,
        city=city,
        condition=condition,
        image=filename,
        user_id=user_id
    )


    db.add(product)

    db.commit()

    db.close()


    return RedirectResponse(
        "/",
        status_code=303
    )



@router.get("/mes-annonces")
def mes_annonces(request: Request):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)


    db = SessionLocal()

    products = db.query(Product).filter(
        Product.user_id == user_id
    ).all()


    db.close()


    return templates.TemplateResponse(
        request=request,
        name="mes_annonces.html",
        context={
            "products": products
        }
    )



@router.get("/modifier-produit/{product_id}")
def modifier_page(request: Request, product_id: int):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)


    db = SessionLocal()

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()


    db.close()


    if not product:
        return RedirectResponse("/mes-annonces", status_code=303)


    return templates.TemplateResponse(
        request=request,
        name="modifier_produit.html",
        context={
            "product": product
        }
    )



@router.post("/modifier-produit/{product_id}")
def modifier_produit(
    request: Request,
    product_id: int,

    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    city: str = Form(...),
    condition: str = Form(...)
):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)


    db = SessionLocal()


    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()


    if not product:
        db.close()
        return RedirectResponse("/mes-annonces", status_code=303)


    product.title = title
    product.description = description
    product.price = price
    product.city = city
    product.condition = condition


    db.commit()

    db.close()


    return RedirectResponse(
        "/mes-annonces",
        status_code=303
    )



@router.get("/supprimer-produit/{product_id}")
def supprimer_produit(request: Request, product_id: int):

    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)


    db = SessionLocal()


    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()


    if product:
        db.delete(product)
        db.commit()


    db.close()


    return RedirectResponse(
        "/mes-annonces",
        status_code=303
    )
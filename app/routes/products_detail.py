from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import joinedload
<<<<<<< HEAD

from app.database.database import SessionLocal
from app.models.product import Product


=======
from app.database.database import SessionLocal
from app.models.product import Product

>>>>>>> 99097da8588bad065ab8d809dfcaa1575e8a71b5
router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/produit/{product_id}")
async def detail_produit(request: Request, product_id: int):

    db = SessionLocal()

<<<<<<< HEAD

    product = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.user)
=======
    product = db.query(Product).options(
        joinedload(Product.category)
>>>>>>> 99097da8588bad065ab8d809dfcaa1575e8a71b5
    ).filter(
        Product.id == product_id
    ).first()

<<<<<<< HEAD

    db.close()


    if not product:
        return {"message": "Produit introuvable"}


=======
    db.close()

>>>>>>> 99097da8588bad065ab8d809dfcaa1575e8a71b5
    return templates.TemplateResponse(
        request=request,
        name="detail_product.html",
        context={
            "product": product
        }
<<<<<<< HEAD
    )
=======
    )
>>>>>>> 99097da8588bad065ab8d809dfcaa1575e8a71b5

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import joinedload

from app.database.database import SessionLocal
from app.models.product import Product


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/produit/{product_id}")
async def detail_produit(request: Request, product_id: int):

    db = SessionLocal()

    product = (
        db.query(Product)
        .options(
            joinedload(Product.category),
            joinedload(Product.user)
        )
        .filter(Product.id == product_id)
        .first()
    )

    db.close()

    if not product:
        return {"message": "Produit introuvable"}

    # Récupérer le message de la session
    message = request.session.pop("message", None)

    # Compteur du panier
    panier = request.session.get("panier", [])
    panier_count = len(panier)

    return templates.TemplateResponse(
        request=request,
        name="detail_product.html",
        context={
            "product": product,
            "message": message,
            "panier_count": panier_count
        }
    )
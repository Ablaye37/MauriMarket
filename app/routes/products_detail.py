
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import joinedload

from app.database.database import SessionLocal
from app.models.product import Product

from app.translations.fr import TRANSLATIONS as FR
from app.translations.ar import TRANSLATIONS as AR


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =========================================================
# LANGUE
# =========================================================

def get_language(request: Request):
    lang = request.query_params.get(
        "lang",
        "fr"
    )

    if lang not in ("fr", "ar"):
        lang = "fr"

    translations = AR if lang == "ar" else FR

    return lang, translations


# =========================================================
# DÉTAIL DU PRODUIT
# =========================================================

@router.get("/produit/{product_id}")
async def detail_produit(
    request: Request,
    product_id: int
):

    db = SessionLocal()

    try:
        product = (
            db.query(Product)
            .options(
                joinedload(Product.category),
                joinedload(Product.user)
            )
            .filter(
                Product.id == product_id
            )
            .first()
        )

    finally:
        db.close()

    # =====================================================
    # PRODUIT INTROUVABLE
    # =====================================================

    if not product:

        lang, translations = get_language(
            request
        )

        return templates.TemplateResponse(
            request=request,
            name="product_detail.html",
            context={
                "product": None,
                "message": translations.get(
                    "not_found",
                    (
                        "Produit introuvable."
                        if lang == "fr"
                        else "المنتج غير موجود."
                    )
                ),
                "panier_count": 0,
                "t": translations,
                "lang": lang
            }
        )

    # =====================================================
    # LANGUE
    # =====================================================

    lang, translations = get_language(
        request
    )

    # =====================================================
    # MESSAGE APRÈS AJOUT AU PANIER
    #
    # Le message est déclenché par ?added=1
    # et ne passe plus par la session.
    # =====================================================

    message = None

    if request.query_params.get("added") == "1":

        message = translations.get(
            "product_added_to_cart",
            (
                "Produit ajouté au panier avec succès."
                if lang == "fr"
                else "تمت إضافة المنتج إلى السلة بنجاح."
            )
        )

    # =====================================================
    # PANIER
    # =====================================================

    panier = request.session.get(
        "panier",
        []
    )

    if not isinstance(
        panier,
        list
    ):
        panier = []

    panier_count = len(
        panier
    )

    # =====================================================
    # AFFICHAGE DU PRODUIT
    # =====================================================

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={
            "product": product,
            "message": message,
            "panier_count": panier_count,
            "t": translations,
            "lang": lang
        }
    )

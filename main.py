from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database.database import SessionLocal

from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.product import Product
from app.models.boutique import Boutique

from app.routes.products import router as products_router
from app.routes import publish
from app.routes import products_detail
from app.routes import auth
from app.routes import categories
from app.routes import cart
from app.routes import admin
from app.routes import boutiques
from app.routes import contact
from app.models.contact_message import ContactMessage

from startup import init_database


# =====================================================
# APPLICATION
# =====================================================

app = FastAPI(
    title="MauriMarket",
    description="Le marché numérique de la Mauritanie",
    version="1.0.0"
)


# =====================================================
# INITIALISATION DE LA BASE DE DONNÉES
# =====================================================

init_database()


# =====================================================
# SESSION
# =====================================================

app.add_middleware(
    SessionMiddleware,
    secret_key="maurimarket-secret"
)


# =====================================================
# FICHIERS STATIQUES
# =====================================================

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


# =====================================================
# TEMPLATES
# =====================================================

templates = Jinja2Templates(
    directory="app/templates"
)


# =====================================================
# CONTEXTE GLOBAL
#
# Ces informations seront disponibles sur toutes
# les pages qui utilisent ce contexte.
# =====================================================

def contexte_global(request: Request):

    # -------------------------------------------------
    # UTILISATEUR CONNECTÉ
    # -------------------------------------------------

    user_id = request.session.get(
        "user_id"
    )

    user_name = request.session.get(
        "user_name"
    )


    # -------------------------------------------------
    # VÉRIFIER SI L'UTILISATEUR POSSÈDE UNE BOUTIQUE
    # -------------------------------------------------

    has_boutique = False

    if user_id:

        db = SessionLocal()

        try:

            boutique = (
                db.query(Boutique)
                .filter(
                    Boutique.user_id == user_id
                )
                .first()
            )

            if boutique:

                has_boutique = True

        finally:

            db.close()


    # -------------------------------------------------
    # PANIER
    # -------------------------------------------------

    panier = request.session.get(
        "panier",
        []
    )

    panier_count = len(panier)


    # -------------------------------------------------
    # LANGUE
    # -------------------------------------------------

    lang = request.query_params.get(
        "lang",
        "fr"
    )


    # -------------------------------------------------
    # RETOUR
    # -------------------------------------------------

    return {
        "user_name": user_name,
        "has_boutique": has_boutique,
        "panier_count": panier_count,
        "lang": lang
    }


# =====================================================
# ACCUEIL
# =====================================================

@app.get("/")
async def home(
    request: Request,
    q: str = Query(default="")
):

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # CATÉGORIES
        # -------------------------------------------------

        categories = (
            db.query(Category)
            .order_by(Category.id)
            .all()
        )


        # -------------------------------------------------
        # SOUS-CATÉGORIES
        # -------------------------------------------------

        categories_data = []

        for category in categories:

            subcategories = (
                db.query(SubCategory)
                .filter(
                    SubCategory.category_id == category.id
                )
                .order_by(SubCategory.id)
                .all()
            )

            categories_data.append({
                "category": category,
                "subcategories": subcategories
            })


        # -------------------------------------------------
        # ANNONCES DE L'ACCUEIL
        #
        # IMPORTANT :
        #
        # boutique_id = NULL
        # → annonce publiée dans l'accueil
        #
        # boutique_id != NULL
        # → produit appartenant à une boutique
        # -------------------------------------------------

        query_products = (
            db.query(Product)
            .filter(
                Product.boutique_id.is_(None)
            )
        )


        # -------------------------------------------------
        # RECHERCHE
        # -------------------------------------------------

        if q:

            products = (
                query_products
                .filter(
                    (Product.title.ilike(f"%{q}%")) |
                    (Product.description.ilike(f"%{q}%")) |
                    (Product.city.ilike(f"%{q}%"))
                )
                .order_by(
                    Product.id.desc()
                )
                .all()
            )

        else:

            products = (
                query_products
                .order_by(
                    Product.id.desc()
                )
                .all()
            )


        # -------------------------------------------------
        # MESSAGE
        # -------------------------------------------------

        message = request.session.pop(
            "message",
            None
        )


        # -------------------------------------------------
        # CONTEXTE GLOBAL
        # -------------------------------------------------

        global_context = contexte_global(
            request
        )


        # -------------------------------------------------
        # PAGE ACCUEIL
        # -------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                # Données accueil
                "categories": categories,
                "categories_data": categories_data,
                "products": products,
                "q": q,
                "message": message,

                # Données globales
                **global_context
            }
        )

    finally:

        db.close()


# =====================================================
# ROUTES
# =====================================================

app.include_router(
    products_router
)

app.include_router(
    publish.router
)

app.include_router(
    products_detail.router
)

app.include_router(
    auth.router
)

app.include_router(
    categories.router
)

app.include_router(
    cart.router
)

app.include_router(
    admin.router
)

app.include_router(
    boutiques.router
)
app.include_router(
    contact.router
)
app.include_router(
    contact.router
)
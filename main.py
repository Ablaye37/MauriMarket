from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database.database import SessionLocal
from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.product import Product

from app.routes.products import router as products_router
from app.routes import publish
from app.routes import products_detail
from app.routes import auth
from app.routes import categories
from app.routes import cart
from app.routes import contact
from app.routes import admin
from app.routes.boutiques import router as boutiques_router

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
# ACCUEIL
# =====================================================

@app.get("/")
async def home(
    request: Request,
    q: str = Query(default=""),
    page: int = Query(default=1, ge=1)
):

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # RÉCUPÉRER LES CATÉGORIES
        # -------------------------------------------------

        categories = (
            db.query(Category)
            .order_by(Category.id)
            .all()
        )


        # -------------------------------------------------
        # RÉCUPÉRER LES SOUS-CATÉGORIES
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
        # PRODUITS + PAGINATION
        # -------------------------------------------------

        PRODUCTS_PER_PAGE = 30

        # Base de la requête :
        # seules les annonces actives sont visibles
        product_query = (
            db.query(Product)
            .filter(
                Product.is_active == True
            )
        )


        # -------------------------------------------------
        # RECHERCHE
        # -------------------------------------------------

        if q:

            product_query = product_query.filter(
                (Product.title.ilike(f"%{q}%")) |
                (Product.description.ilike(f"%{q}%")) |
                (Product.city.ilike(f"%{q}%"))
            )


        # -------------------------------------------------
        # NOMBRE TOTAL DE PRODUITS
        # -------------------------------------------------

        total_products = product_query.count()


        # -------------------------------------------------
        # NOMBRE TOTAL DE PAGES
        # -------------------------------------------------

        total_pages = (
            (total_products + PRODUCTS_PER_PAGE - 1)
            // PRODUCTS_PER_PAGE
        )


        # -------------------------------------------------
        # SÉCURITÉ PAGE
        # -------------------------------------------------

        if total_pages > 0 and page > total_pages:

            page = total_pages


        # -------------------------------------------------
        # CALCUL OFFSET
        # -------------------------------------------------

        offset = (
            (page - 1)
            * PRODUCTS_PER_PAGE
        )


        # -------------------------------------------------
        # PRODUITS DE LA PAGE ACTUELLE
        # -------------------------------------------------

        products = (
            product_query
            .order_by(
                Product.id.desc()
            )
            .offset(offset)
            .limit(PRODUCTS_PER_PAGE)
            .all()
        )


        # -------------------------------------------------
        # UTILISATEUR CONNECTÉ
        # -------------------------------------------------

        user_name = request.session.get(
            "user_name"
        )


        # -------------------------------------------------
        # MESSAGE
        # -------------------------------------------------

        message = request.session.pop(
            "message",
            None
        )


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
        # AFFICHER LA PAGE D'ACCUEIL
        # -------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "categories": categories,
                "categories_data": categories_data,

                # Produits de la page actuelle
                "products": products,

                # Recherche
                "q": q,

                # Pagination
                "page": page,
                "total_pages": total_pages,
                "total_products": total_products,
                "products_per_page": PRODUCTS_PER_PAGE,

                # Utilisateur
                "user_name": user_name,

                # Message
                "message": message,

                # Panier
                "panier_count": panier_count,

                # Langue
                "lang": lang
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
    contact.router
)

app.include_router(
    boutiques_router
)

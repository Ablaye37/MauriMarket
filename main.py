from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database.database import SessionLocal
from app.models.category import Category
from app.models.product import Product

from app.routes.products import router as products_router
from app.routes import publish
from app.routes import products_detail
from app.routes import auth
from app.routes import categories
from app.routes import cart
from app.routes import admin

from startup import init_database

app = FastAPI(
    title="MauriMarket",
    description="Le marché numérique de la Mauritanie",
    version="1.0.0"
)

# Initialiser la base de données
init_database()

# Session
app.add_middleware(
    SessionMiddleware,
    secret_key="maurimarket-secret"
)

# Fichiers statiques
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
async def home(request: Request, q: str = Query(default="")):
    db = SessionLocal()

    categories = db.query(Category).all()


    if q:
        products = (
            db.query(Product)
            .filter(
                (Product.title.ilike(f"%{q}%")) |
                (Product.description.ilike(f"%{q}%")) |
                (Product.city.ilike(f"%{q}%"))
            )
            .order_by(Product.id.desc())
            .all()
        )
    else:
        products = (
            db.query(Product)
            .order_by(Product.id.desc())
            .all()
        )

    user_name = request.session.get("user_name")
    message = request.session.pop("message", None)

    panier = request.session.get("panier", [])
    panier_count = len(panier)
  

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
       context={
    "categories": categories,
    "products": products,
    "q": q,
    "user_name": user_name,
    "message": message, 
    "panier_count": panier_count,
}
    )


# Routes
app.include_router(products_router)
app.include_router(publish.router)
app.include_router(products_detail.router)
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(cart.router)
app.include_router(admin.router)
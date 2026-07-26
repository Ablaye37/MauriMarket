
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database.database import SessionLocal
from app.models.category import Category
from app.routes.products import router as products_router
from app.models.product import Product
from app.routes import publish
from app.routes import products_detail
from fastapi import FastAPI, Request, Query
from app.routes import auth

app = FastAPI(
    title="MauriMarket",
    description="Le marché numérique de la Mauritanie",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.get("/")
async def home(request: Request, q: str = Query(default="")):
    db = SessionLocal()

    categories = db.query(Category).all()

    if q:
        products = db.query(Product).filter(
            (Product.title.ilike(f"%{q}%")) |
            (Product.description.ilike(f"%{q}%")) |
            (Product.city.ilike(f"%{q}%"))
        ).all()
    else:
        products = db.query(Product).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "categories": categories,
            "products": products,
            "q": q
        }
    )
app.include_router(products_router)
app.include_router(publish.router)
app.include_router(products_detail.router)
app.include_router(auth.router)

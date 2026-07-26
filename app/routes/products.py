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
    return templates.TemplateResponse(
        request=request,
        name="publish.html"
    )


@router.post("/publish")
def create_product(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    city: str = Form(...),
    condition: str = Form(...),
    photo: UploadFile = File(...)
):
    filename = None

    if photo and photo.filename:
        filename = photo.filename

        upload_dir = "app/static/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        photo_path = os.path.join(upload_dir, filename)

        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

    product = Product(
        title=title,
        description=description,
        price=price,
        city=city,
        condition=condition,
        image=filename
    )

    db = SessionLocal()
    db.add(product)
    db.commit()
    db.close()

    return RedirectResponse("/", status_code=303)

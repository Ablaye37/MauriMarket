from fastapi import (
    APIRouter,
    Request,
    Form,
    UploadFile,
    File
)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

import shutil
import os
import uuid

from app.database.database import SessionLocal
from app.models.product import Product
from app.models.boutique import Boutique


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# OUTILS IMAGES
# ============================================================

def save_product_image(photo: UploadFile):
    """
    Sauvegarde une image produit dans :

    app/static/uploads/products/

    Retourne le chemin web :

    /static/uploads/products/nom.ext

    Retourne None si le fichier n'est pas valide.
    """

    if not photo or not photo.filename:
        return None

    extension = os.path.splitext(
        photo.filename
    )[1].lower()

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }

    if extension not in allowed_extensions:
        return None

    filename = (
        f"product_"
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    upload_dir = os.path.join(
        "app",
        "static",
        "uploads",
        "products"
    )

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    photo_path = os.path.join(
        upload_dir,
        filename
    )

    try:

        with open(
            photo_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                photo.file,
                buffer
            )

    except OSError as e:

        print(
            "ERREUR SAUVEGARDE IMAGE PRODUIT :",
            repr(e)
        )

        return None

    return (
        f"/static/uploads/products/{filename}"
    )


def get_local_image_path(image_value):
    """
    Transforme les anciens formats de chemins
    en chemin physique local.

    Formats acceptés :

    nom.webp
    /static/uploads/nom.webp
    /static/uploads/products/nom.webp
    static/uploads/products/nom.webp
    products/nom.webp
    """

    if not image_value:
        return None

    value = str(
        image_value
    ).strip()

    if not value:
        return None

    # --------------------------------------------------------
    # URL EXTERNE
    # --------------------------------------------------------

    if (
        value.startswith("http://")
        or value.startswith("https://")
    ):
        return None

    value = value.replace(
        "\\",
        "/"
    )

    # --------------------------------------------------------
    # /static/...
    # --------------------------------------------------------

    if value.startswith(
        "/static/"
    ):

        value = value[1:]

    # --------------------------------------------------------
    # static/...
    # --------------------------------------------------------

    if value.startswith(
        "static/"
    ):

        return os.path.join(
            "app",
            value
        )

    # --------------------------------------------------------
    # products/...
    # --------------------------------------------------------

    if value.startswith(
        "products/"
    ):

        return os.path.join(
            "app",
            "static",
            "uploads",
            value
        )

    # --------------------------------------------------------
    # ANCIEN NOM DE FICHIER
    # --------------------------------------------------------

    return os.path.join(
        "app",
        "static",
        "uploads",
        "products",
        os.path.basename(
            value
        )
    )


def delete_product_image(image_value):
    """
    Supprime une ancienne image locale
    si elle existe.

    Les images externes ne sont jamais supprimées.
    """

    if not image_value:
        return

    path = get_local_image_path(
        image_value
    )

    if not path:
        return

    if os.path.isfile(path):

        try:

            os.remove(path)

        except OSError as e:

            print(
                "ERREUR SUPPRESSION IMAGE PRODUIT :",
                repr(e)
            )


# ============================================================
# OUTILS AUTHENTIFICATION
# ============================================================

def get_current_user_id(request: Request):
    """
    Retourne l'identifiant de l'utilisateur
    actuellement connecté.
    """

    return request.session.get(
        "user_id"
    )


# ============================================================
# OUTILS BOUTIQUE
# ============================================================

def get_user_boutique(
    db,
    user_id
):
    """
    Retourne uniquement la boutique appartenant
    à l'utilisateur connecté.
    """

    if not user_id:
        return None

    return (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )


# ============================================================
# OUTILS PROPRIÉTÉ PRODUIT CLASSIQUE
# ============================================================

def get_owned_product(
    db,
    product_id,
    user_id
):
    """
    Retourne un produit si et seulement si
    celui-ci appartient à l'utilisateur connecté.

    Vérification :

        Product.user_id == user_id
    """

    if not user_id:
        return None

    return (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.user_id == user_id
        )
        .first()
    )


# ============================================================
# OUTILS PROPRIÉTÉ PRODUIT BOUTIQUE
# ============================================================

def get_owned_boutique_product(
    db,
    product_id,
    user_id
):
    """
    Retourne un produit de boutique uniquement si :

    1. l'utilisateur est connecté ;
    2. il possède une boutique ;
    3. le produit appartient à cet utilisateur ;
    4. le produit appartient à SA boutique.

    Cette double vérification est importante.

    Elle empêche par exemple :

        /boutique/modifier-produit/15

    de modifier le produit 15 si celui-ci appartient
    à une autre boutique.
    """

    if not user_id:
        return None

    boutique = get_user_boutique(
        db,
        user_id
    )

    if not boutique:
        return None

    return (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.user_id == user_id,
            Product.boutique_id == boutique.id
        )
        .first()
    )


# ============================================================
# PAGE PUBLIER
# ============================================================

@router.get("/publish")
def publish_page(
    request: Request
):

    user_id = get_current_user_id(
        request
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="publish.html"
    )


# ============================================================
# CRÉER UN PRODUIT CLASSIQUE
# ============================================================

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

    user_id = get_current_user_id(
        request
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    filename = None

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if photo and photo.filename:

        filename = save_product_image(
            photo
        )

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # PRODUIT CLASSIQUE
        #
        # Une annonce publiée depuis la publication classique
        # n'appartient à aucune boutique.
        # ----------------------------------------------------

        product = Product(
            title=title,
            description=description,
            price=price,
            city=city,
            condition=condition,
            image=filename,
            user_id=user_id,
            boutique_id=None
        )

        db.add(product)

        db.commit()

    except Exception as e:

        db.rollback()

        # Si l'enregistrement DB échoue,
        # l'image nouvellement créée est supprimée.

        if filename:

            delete_product_image(
                filename
            )

        print(
            "ERREUR CRÉATION PRODUIT :",
            repr(e)
        )

    finally:

        db.close()

    return RedirectResponse(
        "/",
        status_code=303
    )


# ============================================================
# MES ANNONCES
# ============================================================

@router.get("/mes-annonces")
def mes_annonces(
    request: Request
):

    user_id = get_current_user_id(
        request
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .filter(
                Product.user_id == user_id
            )
            .order_by(
                Product.id.desc()
            )
            .all()
        )

    finally:

        db.close()

    return templates.TemplateResponse(
        request=request,
        name="mes_annonces.html",
        context={
            "products": products
        }
    )


# ============================================================
# MODIFIER PRODUIT CLASSIQUE - PAGE
# ============================================================

@router.get(
    "/modifier-produit/{product_id}"
)
def modifier_page(
    request: Request,
    product_id: int
):

    user_id = get_current_user_id(
        request
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        product = get_owned_product(
            db,
            product_id,
            user_id
        )

        if not product:

            return RedirectResponse(
                "/mes-annonces",
                status_code=303
            )

        return templates.TemplateResponse(
            request=request,
            name="modifier_produit.html",
            context={
                "product": product,
                "produit": product,
                "from_boutique": False
            }
        )

    finally:

        db.close()


# ============================================================
# MODIFIER PRODUIT CLASSIQUE
# ============================================================

@router.post(
    "/modifier-produit/{product_id}"
)
def modifier_produit(
    request: Request,
    product_id: int,

    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    city: str = Form(...),
    condition: str = Form(...),

    photo: UploadFile = File(None)
):

    user_id = get_current_user_id(
        request
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    new_image = None
    old_image = None

    try:

        # ----------------------------------------------------
        # VÉRIFICATION PROPRIÉTAIRE
        # ----------------------------------------------------

        product = get_owned_product(
            db,
            product_id,
            user_id
        )

        if not product:

            return RedirectResponse(
                "/mes-annonces",
                status_code=303
            )

        # ----------------------------------------------------
        # INFORMATIONS
        # ----------------------------------------------------

        product.title = title
        product.description = description
        product.price = price
        product.city = city
        product.condition = condition

        # ----------------------------------------------------
        # NOUVELLE IMAGE
        # ----------------------------------------------------

        if photo and photo.filename:

            new_image = save_product_image(
                photo
            )

            if new_image:

                old_image = product.image

                product.image = new_image

        # ----------------------------------------------------
        # SAUVEGARDE
        # ----------------------------------------------------

        db.commit()

        # ----------------------------------------------------
        # SUPPRESSION DE L'ANCIENNE IMAGE
        #
        # On attend que le commit DB soit réussi.
        # ----------------------------------------------------

        if new_image and old_image:

            delete_product_image(
                old_image
            )

    except Exception as e:

        db.rollback()

        # Si la DB échoue, on supprime uniquement
        # la nouvelle image qui n'est finalement pas utilisée.

        if new_image:

            delete_product_image(
                new_image
            )

        print(
            "ERREUR MODIFICATION PRODUIT :",
            repr(e)
        )

    finally:

        db.close()

    return RedirectResponse(
        "/mes-annonces",
        status_code=303
    )


# ============================================================
# SUPPRIMER PRODUIT CLASSIQUE
# ============================================================

@router.get(
    "/supprimer-produit/{product_id}"
)
def supprimer_produit(
    request: Request,
    product_id: int
):

    user_id = get_current_user_id(
        request
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # VÉRIFICATION PROPRIÉTAIRE
        # ----------------------------------------------------

        product = get_owned_product(
            db,
            product_id,
            user_id
        )

        # ----------------------------------------------------
        # SI LE PRODUIT N'APPARTIENT PAS À L'UTILISATEUR
        #
        # AUCUNE SUPPRESSION
        # ----------------------------------------------------

        if not product:

            return RedirectResponse(
                "/mes-annonces",
                status_code=303
            )

        image = product.image

        db.delete(product)

        db.commit()

        # ----------------------------------------------------
        # SUPPRESSION IMAGE APRÈS COMMIT
        # ----------------------------------------------------

        if image:

            delete_product_image(
                image
            )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR SUPPRESSION PRODUIT :",
            repr(e)
        )

    finally:

        db.close()

    return RedirectResponse(
        "/mes-annonces",
        status_code=303
    )


# ============================================================
# MODIFIER PRODUIT BOUTIQUE - PAGE
# ============================================================

@router.get(
    "/boutique/modifier-produit/{product_id}"
)
def modifier_produit_boutique_page(
    request: Request,
    product_id: int
):

    user_id = get_current_user_id(
        request
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # BOUTIQUE DU PROPRIÉTAIRE
        # ----------------------------------------------------

        boutique = get_user_boutique(
            db,
            user_id
        )

        if not boutique:

            return RedirectResponse(
                "/boutiques",
                status_code=303
            )

        # ----------------------------------------------------
        # PRODUIT DE SA PROPRE BOUTIQUE
        # ----------------------------------------------------

        product = get_owned_boutique_product(
            db,
            product_id,
            user_id
        )

        if not product:

            return RedirectResponse(
                "/ma-boutique",
                status_code=303
            )

        # ----------------------------------------------------
        # PAGE DE MODIFICATION
        # ----------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="modifier_produit.html",
            context={
                "product": product,
                "produit": product,
                "boutique": boutique,
                "from_boutique": True
            }
        )

    finally:

        db.close()


# ============================================================
# ENREGISTRER MODIFICATION PRODUIT BOUTIQUE
# ============================================================

@router.post(
    "/boutique/modifier-produit/{product_id}"
)
def modifier_produit_boutique(
    request: Request,
    product_id: int,

    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    city: str = Form(...),
    condition: str = Form(...),

    photo: UploadFile = File(None)
):

    user_id = get_current_user_id(
        request
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    new_image = None
    old_image = None

    try:

        # ----------------------------------------------------
        # BOUTIQUE DU PROPRIÉTAIRE
        # ----------------------------------------------------

        boutique = get_user_boutique(
            db,
            user_id
        )

        if not boutique:

            return RedirectResponse(
                "/boutiques",
                status_code=303
            )

        # ----------------------------------------------------
        # DOUBLE VÉRIFICATION
        #
        # 1. user_id
        # 2. boutique_id
        # ----------------------------------------------------

        product = get_owned_boutique_product(
            db,
            product_id,
            user_id
        )

        if not product:

            return RedirectResponse(
                "/ma-boutique",
                status_code=303
            )

        # ----------------------------------------------------
        # INFORMATIONS
        # ----------------------------------------------------

        product.title = title
        product.description = description
        product.price = price
        product.city = city
        product.condition = condition

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        if photo and photo.filename:

            new_image = save_product_image(
                photo
            )

            if new_image:

                old_image = product.image

                product.image = new_image

        # ----------------------------------------------------
        # SAUVEGARDE
        # ----------------------------------------------------

        db.commit()

        # ----------------------------------------------------
        # ANCIENNE IMAGE
        # ----------------------------------------------------

        if new_image and old_image:

            delete_product_image(
                old_image
            )

    except Exception as e:

        db.rollback()

        # Si la DB échoue,
        # la nouvelle image n'est pas conservée.

        if new_image:

            delete_product_image(
                new_image
            )

        print(
            "ERREUR MODIFICATION PRODUIT BOUTIQUE :",
            repr(e)
        )

    finally:

        db.close()

    return RedirectResponse(
        "/ma-boutique",
        status_code=303
    )


# ============================================================
# SUPPRIMER PRODUIT BOUTIQUE
# ============================================================

@router.get(
    "/boutique/supprimer-produit/{product_id}"
)
def supprimer_produit_boutique(
    request: Request,
    product_id: int
):

    user_id = get_current_user_id(
        request
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # BOUTIQUE DU PROPRIÉTAIRE
        # ----------------------------------------------------

        boutique = get_user_boutique(
            db,
            user_id
        )

        if not boutique:

            return RedirectResponse(
                "/boutiques",
                status_code=303
            )

        # ----------------------------------------------------
        # DOUBLE CONTRÔLE DU PRODUIT
        #
        # Le produit doit :
        #
        # - appartenir à l'utilisateur connecté
        # - appartenir à sa boutique
        # ----------------------------------------------------

        product = get_owned_boutique_product(
            db,
            product_id,
            user_id
        )

        if not product:

            return RedirectResponse(
                "/ma-boutique",
                status_code=303
            )

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        image = product.image

        # ----------------------------------------------------
        # SUPPRESSION DB
        # ----------------------------------------------------

        db.delete(product)

        db.commit()

        # ----------------------------------------------------
        # SUPPRESSION FICHIER APRÈS COMMIT
        # ----------------------------------------------------

        if image:

            delete_product_image(
                image
            )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR SUPPRESSION PRODUIT BOUTIQUE :",
            repr(e)
        )

    finally:

        db.close()

    return RedirectResponse(
        "/ma-boutique",
        status_code=303
    )
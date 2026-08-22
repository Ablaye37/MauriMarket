from uuid import uuid4
from pathlib import Path

from fastapi import (
    APIRouter,
    Request,
    Depends,
    UploadFile,
    File,
    Form,
)

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.boutique import Boutique
from app.models.boutique_request import BoutiqueRequest
from app.models.product import Product


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# TEMPLATES
# ============================================================

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# DOSSIER DES IMAGES
# ============================================================

BOUTIQUE_UPLOAD_DIR = Path(
    "app/static/uploads/boutiques"
)


# ============================================================
# TYPES D'IMAGES AUTORISÉS
# ============================================================

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


# ============================================================
# DATABASE
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# CONTEXTE GLOBAL
# ============================================================

def contexte_global(
    request: Request,
    db: Session
):

    user_id = request.session.get("user_id")
    user_name = request.session.get("user_name")

    has_boutique = False
    boutique_request = None

    # --------------------------------------------------------
    # UTILISATEUR CONNECTÉ
    # --------------------------------------------------------

    if user_id:

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

        has_boutique = boutique is not None

        # ----------------------------------------------------
        # DERNIÈRE DEMANDE DE BOUTIQUE
        # ----------------------------------------------------

        boutique_request = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.user_id == user_id
            )
            .order_by(
                BoutiqueRequest.id.desc()
            )
            .first()
        )

    # --------------------------------------------------------
    # PANIER
    # --------------------------------------------------------

    panier = request.session.get(
        "panier",
        []
    )

    panier_count = len(panier)

    # --------------------------------------------------------
    # LANGUE
    # --------------------------------------------------------

    lang = request.query_params.get(
        "lang",
        "fr"
    )

    return {
        "user_id": user_id,
        "user_name": user_name,
        "has_boutique": has_boutique,
        "boutique_request": boutique_request,
        "panier_count": panier_count,
        "lang": lang,
    }


# ============================================================
# LISTE DES BOUTIQUES
# ============================================================

@router.get("/boutiques")
async def boutiques(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
):

    query = db.query(Boutique)

    # --------------------------------------------------------
    # RECHERCHE
    # --------------------------------------------------------

    if q:

        search = f"%{q}%"

        query = query.filter(
            (Boutique.name.ilike(search))
            |
            (Boutique.category.ilike(search))
            |
            (Boutique.sale_type.ilike(search))
            |
            (Boutique.city.ilike(search))
        )

    # --------------------------------------------------------
    # RÉCUPÉRATION
    # --------------------------------------------------------

    boutiques_list = (
        query
        .order_by(
            Boutique.id.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # CONTEXTE
    # --------------------------------------------------------

    context = contexte_global(
        request,
        db
    )

    context.update({
        "request": request,
        "boutiques": boutiques_list,
        "q": q,
    })

    return templates.TemplateResponse(
        request=request,
        name="boutiques.html",
        context=context,
    )


# ============================================================
# CRÉER UNE BOUTIQUE — PAGE
# ============================================================

@router.get("/boutique/creer")
async def page_creer_boutique(
    request: Request,
    db: Session = Depends(get_db),
):

    user_id = request.session.get(
        "user_id"
    )

    # --------------------------------------------------------
    # NON CONNECTÉ
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    # --------------------------------------------------------
    # VÉRIFIER SI L'UTILISATEUR A DÉJÀ UNE BOUTIQUE
    # --------------------------------------------------------

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    if boutique:

        return RedirectResponse(
            url="/ma-boutique",
            status_code=303,
        )

    # --------------------------------------------------------
    # VÉRIFIER UNE DEMANDE EN ATTENTE
    # --------------------------------------------------------

    demande = (
        db.query(BoutiqueRequest)
        .filter(
            BoutiqueRequest.user_id == user_id,
            BoutiqueRequest.status == "pending",
        )
        .order_by(
            BoutiqueRequest.id.desc()
        )
        .first()
    )

    if demande:

        return RedirectResponse(
            url="/boutique/demande",
            status_code=303,
        )

    # --------------------------------------------------------
    # AFFICHER LA PAGE
    # --------------------------------------------------------

    context = contexte_global(
        request,
        db
    )

    context["request"] = request

    return templates.TemplateResponse(
        request=request,
        name="creer_boutique.html",
        context=context,
    )


# ============================================================
# CRÉER UNE DEMANDE DE BOUTIQUE
# ============================================================

@router.post("/boutique/creer")
async def creer_boutique(
    request: Request,

    name: str = Form(...),

    category: str = Form(""),

    sale_type: str = Form(""),

    db: Session = Depends(get_db),
):

    user_id = request.session.get(
        "user_id"
    )

    # --------------------------------------------------------
    # NON CONNECTÉ
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    # --------------------------------------------------------
    # DÉJÀ UNE BOUTIQUE
    # --------------------------------------------------------

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    if boutique:

        return RedirectResponse(
            url="/ma-boutique",
            status_code=303,
        )

    # --------------------------------------------------------
    # DEMANDE DÉJÀ EN ATTENTE
    # --------------------------------------------------------

    demande_existante = (
        db.query(BoutiqueRequest)
        .filter(
            BoutiqueRequest.user_id == user_id,
            BoutiqueRequest.status == "pending",
        )
        .first()
    )

    if demande_existante:

        return RedirectResponse(
            url="/boutique/demande",
            status_code=303,
        )

    # --------------------------------------------------------
    # CRÉER LA DEMANDE
    # --------------------------------------------------------

    demande = BoutiqueRequest(
        name=name.strip(),
        category=category.strip(),
        sale_type=sale_type.strip(),
        user_id=user_id,
        status="pending",
    )

    db.add(demande)
    db.commit()

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    request.session["message"] = (
        "Votre demande de boutique a été envoyée."
    )

    return RedirectResponse(
        url="/boutique/demande",
        status_code=303,
    )


# ============================================================
# STATUT DE LA DEMANDE
# ============================================================

@router.get("/boutique/demande")
async def statut_demande(
    request: Request,
    db: Session = Depends(get_db),
):

    user_id = request.session.get(
        "user_id"
    )

    # --------------------------------------------------------
    # NON CONNECTÉ
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    # --------------------------------------------------------
    # DERNIÈRE DEMANDE
    # --------------------------------------------------------

    demande = (
        db.query(BoutiqueRequest)
        .filter(
            BoutiqueRequest.user_id == user_id
        )
        .order_by(
            BoutiqueRequest.id.desc()
        )
        .first()
    )

    # --------------------------------------------------------
    # CONTEXTE
    # --------------------------------------------------------

    context = contexte_global(
        request,
        db
    )

    context.update({
        "request": request,
        "demande": demande,
    })

    return templates.TemplateResponse(
        request=request,
        name="publier_boutique.html",
        context=context,
    )


# ============================================================
# MA BOUTIQUE
# ============================================================

@router.get("/ma-boutique")
async def ma_boutique(
    request: Request,
    db: Session = Depends(get_db),
):

    user_id = request.session.get(
        "user_id"
    )

    # --------------------------------------------------------
    # NON CONNECTÉ
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    # --------------------------------------------------------
    # RÉCUPÉRER LA BOUTIQUE DU PROPRIÉTAIRE
    # --------------------------------------------------------

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    # --------------------------------------------------------
    # AUCUNE BOUTIQUE
    # --------------------------------------------------------

    if not boutique:

        return RedirectResponse(
            url="/boutique/creer",
            status_code=303,
        )

    # --------------------------------------------------------
    # PRODUITS DE CETTE BOUTIQUE UNIQUEMENT
    # --------------------------------------------------------

    products = (
        db.query(Product)
        .filter(
            Product.boutique_id == boutique.id
        )
        .order_by(
            Product.id.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # CONTEXTE
    # --------------------------------------------------------

    context = contexte_global(
        request,
        db
    )

    context.update({
        "request": request,
        "boutique": boutique,
        "products": products,
    })

    return templates.TemplateResponse(
        request=request,
        name="ma_boutique.html",
        context=context,
    )


# ============================================================
# MODIFIER MA BOUTIQUE — PAGE
# ============================================================

@router.get("/ma-boutique/modifier")
async def page_modifier_boutique(
    request: Request,
    db: Session = Depends(get_db),
):

    user_id = request.session.get(
        "user_id"
    )

    # --------------------------------------------------------
    # NON CONNECTÉ
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    # --------------------------------------------------------
    # RÉCUPÉRER UNIQUEMENT SA BOUTIQUE
    # --------------------------------------------------------

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    if not boutique:

        return RedirectResponse(
            url="/boutique/creer",
            status_code=303,
        )

    # --------------------------------------------------------
    # CONTEXTE
    # --------------------------------------------------------

    context = contexte_global(
        request,
        db
    )

    context.update({
        "request": request,
        "boutique": boutique,
    })

    return templates.TemplateResponse(
        request=request,
        name="modifier_boutique.html",
        context=context,
    )


# ============================================================
# MODIFIER MA BOUTIQUE
# ============================================================

@router.post("/ma-boutique/modifier")
async def modifier_boutique(
    request: Request,

    name: str = Form(...),

    category: str = Form(""),

    sale_type: str = Form(""),

    description: str = Form(""),

    city: str = Form(""),

    logo: UploadFile | None = File(None),

    cover_image: UploadFile | None = File(None),

    db: Session = Depends(get_db),
):

    user_id = request.session.get(
        "user_id"
    )

    # --------------------------------------------------------
    # NON CONNECTÉ
    # --------------------------------------------------------

    if not user_id:

        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    # --------------------------------------------------------
    # RÉCUPÉRER UNIQUEMENT SA BOUTIQUE
    # --------------------------------------------------------

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.user_id == user_id
        )
        .first()
    )

    if not boutique:

        return RedirectResponse(
            url="/boutique/creer",
            status_code=303,
        )

    # --------------------------------------------------------
    # INFORMATIONS
    # --------------------------------------------------------

    boutique.name = name.strip()

    # On conserve category pour compatibilité avec
    # la base actuelle, mais on ne développe pas cette
    # fonctionnalité pour l'instant.
    boutique.category = category.strip()

    boutique.sale_type = sale_type.strip()

    boutique.description = description.strip()

    boutique.city = city.strip()

    # --------------------------------------------------------
    # CRÉER LE DOSSIER
    # --------------------------------------------------------

    BOUTIQUE_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    if logo and logo.filename:

        extension = ALLOWED_IMAGE_TYPES.get(
            logo.content_type
        )

        if extension:

            filename = (
                f"boutique_{boutique.id}_"
                f"logo_{uuid4().hex}"
                f"{extension}"
            )

            file_path = (
                BOUTIQUE_UPLOAD_DIR / filename
            )

            content = await logo.read()

            with open(
                file_path,
                "wb"
            ) as file:

                file.write(content)

            boutique.logo = (
                f"/static/uploads/boutiques/{filename}"
            )

    # --------------------------------------------------------
    # IMAGE DE COUVERTURE
    # --------------------------------------------------------

    if cover_image and cover_image.filename:

        extension = ALLOWED_IMAGE_TYPES.get(
            cover_image.content_type
        )

        if extension:

            filename = (
                f"boutique_{boutique.id}_"
                f"cover_{uuid4().hex}"
                f"{extension}"
            )

            file_path = (
                BOUTIQUE_UPLOAD_DIR / filename
            )

            content = await cover_image.read()

            with open(
                file_path,
                "wb"
            ) as file:

                file.write(content)

            boutique.cover_image = (
                f"/static/uploads/boutiques/{filename}"
            )

    # --------------------------------------------------------
    # SAUVEGARDER
    # --------------------------------------------------------

    db.commit()
    db.refresh(boutique)

    request.session["message"] = (
        "Votre boutique a été modifiée avec succès."
    )

    return RedirectResponse(
        url="/ma-boutique",
        status_code=303,
    )


# ============================================================
# DÉTAIL D'UNE BOUTIQUE
# ============================================================

@router.get("/boutique/detail/{boutique_id}")
async def boutique_detail(
    boutique_id: int,
    request: Request,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # RÉCUPÉRER LA BOUTIQUE
    # --------------------------------------------------------

    boutique = (
        db.query(Boutique)
        .filter(
            Boutique.id == boutique_id
        )
        .first()
    )

    if not boutique:

        return RedirectResponse(
            url="/boutiques",
            status_code=303,
        )

    # --------------------------------------------------------
    # PRODUITS DE LA BOUTIQUE
    # --------------------------------------------------------

    products = (
        db.query(Product)
        .filter(
            Product.boutique_id == boutique.id
        )
        .order_by(
            Product.id.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # CONTEXTE
    # --------------------------------------------------------

    context = contexte_global(
        request,
        db
    )

    context.update({
    "request": request,             
    "boutique": boutique,
    "products": products,
    "produits": products,
    })
    return templates.TemplateResponse(
        request=request,
        name="boutique_detail.html",
        context=context,
    )


# ============================================================
# COMPATIBILITÉ AVEC L'ANCIEN LIEN
# ============================================================
#
# Ancienne URL :
#
#     /boutique/5
#
# Nouvelle URL :
#
#     /boutique/detail/5
#
# On garde l'ancienne route pour éviter de casser
# d'anciens liens.
# ============================================================

@router.get("/boutique/{boutique_id}")
async def boutique_detail_ancien_lien(
    boutique_id: int,
    request: Request,
    db: Session = Depends(get_db),
):

    return await boutique_detail(
        boutique_id=boutique_id,
        request=request,
        db=db,
    )
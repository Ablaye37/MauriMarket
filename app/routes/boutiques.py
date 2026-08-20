from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.database import SessionLocal
from app.models.boutique import Boutique
from app.models.boutique_request import BoutiqueRequest
from app.models.product import Product

import os
import uuid


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =====================================================
# CONTEXTE GLOBAL
# =====================================================

def contexte_global(request: Request, db):

    user_id = request.session.get("user_id")
    user_name = request.session.get("user_name")

    has_boutique = False
    boutique_request = None

    if user_id:

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

        if boutique:
            has_boutique = True

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

    panier = request.session.get(
        "panier",
        []
    )

    panier_count = len(panier)

    lang = request.query_params.get(
        "lang",
        "fr"
    )

    return {
        "user_name": user_name,
        "has_boutique": has_boutique,
        "boutique_request": boutique_request,
        "panier_count": panier_count,
        "lang": lang
    }


# =====================================================
# UTILITAIRE : SAUVEGARDER UNE IMAGE
# =====================================================

async def sauvegarder_image(
    fichier: UploadFile,
    prefix: str,
    boutique_id: int
):

    if not fichier or not fichier.filename:
        return None

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp"
    }

    extension = allowed_types.get(
        fichier.content_type
    )

    if not extension:
        return None

    upload_dir = "app/static/uploads/boutiques"

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    filename = (
        f"boutique_{boutique_id}_"
        f"{prefix}_"
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = os.path.join(
        upload_dir,
        filename
    )

    content = await fichier.read()

    if not content:
        return None

    with open(
        file_path,
        "wb"
    ) as f:
        f.write(content)

    return (
        f"/static/uploads/boutiques/{filename}"
    )


# =====================================================
# LISTE DES BOUTIQUES
# =====================================================

@router.get("/boutiques")
async def liste_boutiques(
    request: Request,
    q: str = ""
):

    db = SessionLocal()

    try:

        search_query = q.strip()

        boutique_query = db.query(Boutique)

        if search_query:

            recherche = f"%{search_query}%"

            boutique_query = boutique_query.filter(
                (Boutique.name.ilike(recherche))
                |
                (Boutique.sale_type.ilike(recherche))
                |
                (Boutique.city.ilike(recherche))
            )

        boutiques = (
            boutique_query
            .order_by(
                Boutique.id.desc()
            )
            .all()
        )

        user_id = request.session.get(
            "user_id"
        )

        ma_boutique = None

        if user_id:

            ma_boutique = (
                db.query(Boutique)
                .filter(
                    Boutique.user_id == user_id
                )
                .first()
            )

        global_context = contexte_global(
            request,
            db
        )

        return templates.TemplateResponse(
            request=request,
            name="boutiques.html",
            context={
                "boutiques": boutiques,
                "ma_boutique": ma_boutique,
                "search_query": search_query,
                **global_context
            }
        )

    finally:

        db.close()

# =====================================================
# VOIR UNE BOUTIQUE PUBLIQUEMENT
# =====================================================

@router.get("/boutique/{boutique_id}")
async def voir_boutique(
    request: Request,
    boutique_id: int
):

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # RÉCUPÉRER LA BOUTIQUE
        # -------------------------------------------------

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.id == boutique_id
            )
            .first()
        )

        # -------------------------------------------------
        # BOUTIQUE INTROUVABLE
        # -------------------------------------------------

        if not boutique:

            return RedirectResponse(
                "/boutiques",
                status_code=303
            )

        # -------------------------------------------------
        # PRODUITS DE LA BOUTIQUE
        # -------------------------------------------------

        produits = (
            db.query(Product)
            .filter(
                Product.boutique_id == boutique.id
            )
            .order_by(
                Product.id.desc()
            )
            .all()
        )

        # -------------------------------------------------
        # CONTEXTE GLOBAL
        # -------------------------------------------------

        global_context = contexte_global(
            request,
            db
        )

        # -------------------------------------------------
        # PAGE PUBLIQUE
        # -------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="boutique_detail.html",
            context={
                "boutique": boutique,
                "produits": produits,
                **global_context
            }
        )

    finally:

        db.close()

# =====================================================
# PAGE CRÉER UNE BOUTIQUE
# =====================================================

@router.get("/boutique/creer")
async def page_creer_boutique(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

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

            return RedirectResponse(
                "/ma-boutique",
                status_code=303
            )

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

        if demande and demande.status == "pending":

            return RedirectResponse(
                "/boutique/demande",
                status_code=303
            )

        global_context = contexte_global(
            request,
            db
        )

        return templates.TemplateResponse(
            request=request,
            name="creer_boutique.html",
            context={
                **global_context
            }
        )

    finally:

        db.close()


# =====================================================
# ENVOYER UNE DEMANDE DE BOUTIQUE
# =====================================================

@router.post("/boutique/creer")
async def creer_boutique(
    request: Request,
    name: str = Form(...),
    sale_type: str = Form(...)
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    name = name.strip()
    sale_type = sale_type.strip()

    if not name or not sale_type:

        return RedirectResponse(
            "/boutique/creer",
            status_code=303
        )

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

            return RedirectResponse(
                "/ma-boutique",
                status_code=303
            )

        demande_en_attente = (
            db.query(BoutiqueRequest)
            .filter(
                BoutiqueRequest.user_id == user_id,
                BoutiqueRequest.status == "pending"
            )
            .first()
        )

        if demande_en_attente:

            return RedirectResponse(
                "/boutique/demande",
                status_code=303
            )

        demande = BoutiqueRequest(
            name=name,
            sale_type=sale_type,
            user_id=user_id,
            status="pending"
        )

        db.add(demande)

        db.commit()

        db.refresh(demande)

        request.session["message"] = (
            "Votre demande de boutique a été envoyée. "
            "Elle sera examinée par l'administrateur."
        )

        return RedirectResponse(
            "/boutique/demande",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR DEMANDE BOUTIQUE :",
            e
        )

        request.session["message"] = (
            "Impossible d'envoyer la demande."
        )

        return RedirectResponse(
            "/boutique/creer",
            status_code=303
        )

    finally:

        db.close()


# =====================================================
# STATUT DE LA DEMANDE
# =====================================================

@router.get("/boutique/demande")
async def statut_demande(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

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

            return RedirectResponse(
                "/ma-boutique",
                status_code=303
            )

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

        global_context = contexte_global(
            request,
            db
        )

        message = request.session.pop(
            "message",
            None
        )

        return templates.TemplateResponse(
            request=request,
            name="publier_boutique.html",
            context={
                "demande": demande,
                "message": message,
                **global_context
            }
        )

    finally:

        db.close()


# =====================================================
# MA BOUTIQUE
# =====================================================

@router.get("/ma-boutique")
async def ma_boutique(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

        if not boutique:

            return RedirectResponse(
                "/boutique/creer",
                status_code=303
            )

        produits = (
            db.query(Product)
            .filter(
                Product.boutique_id == boutique.id
            )
            .order_by(
                Product.id.desc()
            )
            .all()
        )

        global_context = contexte_global(
            request,
            db
        )

        return templates.TemplateResponse(
            request=request,
            name="ma_boutique.html",
            context={
                "boutique": boutique,
                "produits": produits,
                "products": produits,
                **global_context
            }
        )

    finally:

        db.close()


# =====================================================
# PAGE MODIFIER MA BOUTIQUE
# =====================================================

@router.get("/ma-boutique/modifier")
async def page_modifier_boutique(
    request: Request
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

        if not boutique:

            return RedirectResponse(
                "/boutique/creer",
                status_code=303
            )

        global_context = contexte_global(
            request,
            db
        )

        return templates.TemplateResponse(
            request=request,
            name="modifier_boutique.html",
            context={
                "boutique": boutique,
                **global_context
            }
        )

    finally:

        db.close()


# =====================================================
# ENREGISTRER LES MODIFICATIONS
# LOGO + COVER
# =====================================================

@router.post("/ma-boutique/modifier")
async def modifier_boutique(
    request: Request,
    name: str = Form(...),
    sale_type: str = Form(...),
    description: str = Form(""),
    city: str = Form(""),
    logo: UploadFile = File(None),
    cover_image: UploadFile = File(None)
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    db = SessionLocal()

    try:

        boutique = (
            db.query(Boutique)
            .filter(
                Boutique.user_id == user_id
            )
            .first()
        )

        if not boutique:

            return RedirectResponse(
                "/boutique/creer",
                status_code=303
            )

        name = name.strip()
        sale_type = sale_type.strip()
        description = description.strip()
        city = city.strip()

        if not name or not sale_type:

            return RedirectResponse(
                "/ma-boutique/modifier",
                status_code=303
            )

        boutique.name = name
        boutique.sale_type = sale_type
        boutique.description = description or None
        boutique.city = city or None

        # =================================================
        # LOGO
        # =================================================

        if logo and logo.filename:

            nouveau_logo = await sauvegarder_image(
                logo,
                "logo",
                boutique.id
            )

            if nouveau_logo:

                boutique.logo = nouveau_logo

        # =================================================
        # COVER
        # =================================================

        if cover_image and cover_image.filename:

            nouvelle_cover = await sauvegarder_image(
                cover_image,
                "cover",
                boutique.id
            )

            if nouvelle_cover:

                boutique.cover_image = nouvelle_cover

        # =================================================
        # ENREGISTRER EN BASE
        # =================================================

        db.commit()

        db.refresh(boutique)

        print(
            "=========================================="
        )

        print(
            "BOUTIQUE MODIFIÉE"
        )

        print(
            "ID :",
            boutique.id
        )

        print(
            "LOGO :",
            boutique.logo
        )

        print(
            "COVER :",
            boutique.cover_image
        )

        print(
            "=========================================="
        )

        return RedirectResponse(
            "/ma-boutique",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        print(
            "ERREUR MODIFICATION BOUTIQUE :",
            repr(e)
        )

        return RedirectResponse(
            "/ma-boutique/modifier",
            status_code=303
        )

    finally:

        db.close()
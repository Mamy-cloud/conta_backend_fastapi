import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.connexion_cloud.connexion_db import get_db
from app.models.base_model_login_mobile import (
    LoginMobileResponse,
    ServerStatusResponse,
)

# ⚠️ IMPORT LAZY (évite crash Render au startup)
def get_verif_login_mobile():
    from app.request_command.verif_login_mobile import verif_login_mobile
    return verif_login_mobile


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/mobile/verif",
    tags=["Mobile — Login"],
)

# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────

@router.get(
    "/status/login/mobile",
    response_model=ServerStatusResponse,
)
def server_status():
    return ServerStatusResponse(
        success=True,
        message="Serveur opérationnel ✅",
    )


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────

@router.post(
    "/login/post/mobile",
    response_model=LoginMobileResponse,
)
def login_mobile(
    payload,
    db: Session = Depends(get_db),
):
    logger.info("LOGIN MOBILE REQUEST")

    try:
        verif_login_mobile = get_verif_login_mobile()

        result = verif_login_mobile(
            db=db,
            identifiant=payload.identifiant,
            password=payload.password,
        )

        # ── VALIDATION SAFE RESULT ──
        if not isinstance(result, dict):
            raise ValueError("Invalid response from verif_login_mobile")

        # ── IDENTIFIANT ──
        if not result.get("identifiant_ok"):
            return LoginMobileResponse(
                success=False,
                identifiant_ok=False,
                password_ok=False,
                user_id=None,
                message="Identifiant incorrect.",
            )

        # ── PASSWORD ──
        if not result.get("password_ok"):
            return LoginMobileResponse(
                success=False,
                identifiant_ok=True,
                password_ok=False,
                user_id=None,
                message="Mot de passe incorrect.",
            )

        # ── USER SAFE ACCESS ──
        user = result.get("user")

        if not user or not hasattr(user, "id"):
            raise ValueError("User missing in response")

        return LoginMobileResponse(
            success=True,
            identifiant_ok=True,
            password_ok=True,
            user_id=user.id,
            message="Connexion réussie ✅",
        )

    except Exception as e:
        logger.error(f"LOGIN ERROR: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail=f"Erreur serveur : {str(e)}",
        )
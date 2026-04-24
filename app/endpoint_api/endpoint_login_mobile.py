# endpoint_login_mobile.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.connexion_db.connexion_db import get_db
from app.models.base_model_login_mobile import (
    LoginMobileRequest,
    LoginMobileResponse,
    ServerStatusResponse,
)
from app.request_command.login.verif_login_mobile import verif_login_mobile

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/mobile/verif",
    tags=["Mobile — Login"],
)


# ─── GET /mobile/verif/status/login/mobile ────────────────────────────────────

@router.get(
    "/status/login/mobile",
    response_model=ServerStatusResponse,
    summary="Vérifie que le serveur est allumé",
    status_code=status.HTTP_200_OK,
)
def server_status():
    """Appelé par le mobile au démarrage. Confirme que FastAPI est opérationnel."""
    logger.info("━━━ GET /mobile/verif/status/login/mobile ━━━")
    return ServerStatusResponse(
        success=True,
        message="Serveur opérationnel ✅",
    )


# ─── POST /mobile/verif/login/post/mobile ────────────────────────────────────

@router.post(
    "/login/post/mobile",
    response_model=LoginMobileResponse,
    summary="Vérifie les identifiants et retourne l'id Supabase",
    status_code=status.HTTP_200_OK,
)
def login_mobile(
    payload: LoginMobileRequest,
    db:      Session = Depends(get_db),
):
    """
    Reçoit {identifiant, password} depuis le mobile.

    Flux :
      1. Cherche l'identifiant dans Supabase login_user
      2. Vérifie le mot de passe
      3. Retourne l'id Supabase → stocké dans SQLite local du mobile
    """
    logger.info("━━━ POST /mobile/verif/login/post/mobile ━━━")
    logger.debug(f"identifiant={payload.identifiant} | password={'*' * len(payload.password)}")

    try:
        result = verif_login_mobile(
            db          = db,
            identifiant = payload.identifiant,
            password    = payload.password,
        )
        logger.debug(f"Résultat verif → {result}")

        # ── Identifiant introuvable ────────────────────────────────────────
        if not result["identifiant_ok"]:
            logger.warning(f"⛔ Identifiant introuvable : {payload.identifiant}")
            return LoginMobileResponse(
                success        = False,
                identifiant_ok = False,
                password_ok    = False,
                user_id        = None,
                message        = "Identifiant incorrect.",
            )

        # ── Mot de passe incorrect ─────────────────────────────────────────
        if not result["password_ok"]:
            logger.warning(f"⚠️  Mot de passe incorrect pour : {payload.identifiant}")
            return LoginMobileResponse(
                success        = False,
                identifiant_ok = True,
                password_ok    = False,
                user_id        = None,
                message        = "Mot de passe incorrect.",
            )

        # ── Connexion réussie → retourne l'id pour SQLite local ───────────
        user = result["user"]
        logger.info(f"✅ Connexion réussie → id={user.id} | identifiant={payload.identifiant}")
        return LoginMobileResponse(
            success        = True,
            identifiant_ok = True,
            password_ok    = True,
            user_id        = user.id,
            message        = "Connexion réussie ✅",
        )

    except Exception as e:
        logger.error(f"💥 Erreur login_mobile : {e}", exc_info=True)
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail      = f"Erreur serveur : {str(e)}",
        )

import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.request_command.request_create_table import LoginUser

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# LOGIN VERIFICATION SAFE
# ─────────────────────────────────────────────

def verif_login_mobile(
    db: Session,
    identifiant: str,
    password: str,
) -> Dict:

    logger.info("LOGIN CHECK START")

    # ───────────── SAFE INPUT LOG ─────────────
    safe_identifiant = identifiant or ""

    logger.debug(f"identifiant={safe_identifiant}")

    # ───────────── QUERY SAFE ─────────────
    user: Optional[LoginUser] = (
        db.query(LoginUser)
        .filter(LoginUser.identifiant == safe_identifiant)
        .first()
    )

    # ───────────── USER NOT FOUND ─────────────
    if not user:
        logger.warning(f"Identifiant introuvable: {safe_identifiant}")

        return {
            "identifiant_ok": False,
            "password_ok": False,
            "user": None,
        }

    # ───────────── PASSWORD CHECK ─────────────
    password_ok = False

    try:
        # ⚠️ version simple (à remplacer par hash plus tard)
        password_ok = (user.password == password)
    except Exception as e:
        logger.error(f"Password check error: {e}")
        password_ok = False

    # ───────────── LOG SAFE ─────────────
    logger.info(
        f"user_found id={user.id} password_ok={password_ok}"
    )

    # ───────────── RETURN SAFE ─────────────
    return {
        "identifiant_ok": True,
        "password_ok": password_ok,
        "user": user if password_ok else None,
    }
# verif_login_mobile.py
import logging
from sqlalchemy.orm import Session
from request_command.request_create_table import LoginUser

logger = logging.getLogger(__name__)


def verif_login_mobile(
    db:          Session,
    identifiant: str,
    password:    str,
) -> dict:
    """
    Vérifie les identifiants dans login_user de Supabase.
    Cherche par identifiant, retourne l'id si tout est correct.
    """
    logger.info("━━━ verif_login_mobile démarré ━━━")
    logger.debug(f"identifiant={identifiant} | password={'*' * len(password)}")

    # 1. Cherche par identifiant ───────────────────────────────────────────────
    logger.debug(f"Requête DB : SELECT * FROM login_user WHERE identifiant='{identifiant}'")
    user = db.query(LoginUser).filter(LoginUser.identifiant == identifiant).first()

    if user is None:
        logger.warning(f"❌ Identifiant introuvable : {identifiant}")
        return {
            "identifiant_ok": False,
            "password_ok":    False,
            "user":           None,
        }

    logger.info(f"✅ Identifiant trouvé : {identifiant} → id={user.id}")

    # 2. Vérifie le mot de passe ───────────────────────────────────────────────
    password_ok = (user.password == password)
    if password_ok:
        logger.info(f"✅ Mot de passe correct pour {identifiant}")
    else:
        logger.warning(f"❌ Mot de passe incorrect pour {identifiant}")

    logger.debug(f"Résultat → identifiant_ok=True | password_ok={password_ok} | user_id={user.id}")

    return {
        "identifiant_ok": True,
        "password_ok":    password_ok,
        "user":           user,
    }

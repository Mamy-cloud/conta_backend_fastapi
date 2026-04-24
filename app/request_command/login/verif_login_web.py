# ================================================
# verif_login_web.py
# Vérifie l'identifiant et le mot de passe
# ================================================

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.connexion_db.connexion_db import engine
from app.request_command.request_create_table import LoginUser
from app.models.base_model_login_web import LoginWebRequest


# Message générique — ne pas préciser si c'est
# l'identifiant ou le mot de passe qui est faux
# (sécurité : évite l'énumération des comptes).
_MSG_INVALID = "Identifiant ou mot de passe incorrect."


def verify_login(data: LoginWebRequest) -> str:
    """
    Vérifie les credentials de l'utilisateur.

    - Si l'identifiant n'existe pas → ValueError
    - Si le mot de passe ne correspond pas → ValueError
    - Si tout est correct → retourne le user_id (str)

    Le message d'erreur est volontairement identique dans
    les deux cas pour ne pas révéler quels comptes existent.
    """

    with Session(engine) as session:
        stmt = select(LoginUser).where(
            LoginUser.identifiant == data.identifiant.strip()
        )
        user = session.scalars(stmt).first()

        # ── Identifiant introuvable ──────────────────────
        if user is None:
            raise ValueError(_MSG_INVALID)

        # ── Mot de passe incorrect ───────────────────────
        if user.password != data.mot_de_passe:
            raise ValueError(_MSG_INVALID)

    return user.id

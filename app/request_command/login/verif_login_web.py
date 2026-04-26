# ================================================
# verif_login_web.py
# Vérifie les credentials et retourne les infos user
# ================================================

from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.connexion_db.connexion_db import engine
from app.request_command.request_create_table import LoginUser
from app.models.base_model_login_web import LoginWebRequest

_MSG_INVALID = "Identifiant ou mot de passe incorrect."


@dataclass
class UserSession:
    user_id:    str
    identifiant: str
    email:      str | None


def verify_login(data: LoginWebRequest) -> UserSession:
    """
    Vérifie les credentials.
    - Identifiant introuvable  → ValueError
    - Mot de passe incorrect   → ValueError
    - OK → retourne UserSession(user_id, identifiant, email)
    """

    with Session(engine) as session:
        stmt = select(LoginUser).where(
            LoginUser.identifiant == data.identifiant.strip()
        )
        user = session.scalars(stmt).first()

        if user is None:
            raise ValueError(_MSG_INVALID)

        if user.password != data.mot_de_passe:
            raise ValueError(_MSG_INVALID)

        return UserSession(
            user_id     = user.id,
            identifiant = user.identifiant,
            email       = user.email,
        )

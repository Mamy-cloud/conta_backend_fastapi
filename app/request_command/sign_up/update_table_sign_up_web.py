# ================================================
# update_table_sign_up_web.py
# Insère un nouvel utilisateur dans login_user
# ================================================

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.connexion_db.connexion_db import engine
from app.request_command.request_create_table import LoginUser
from app.models.base_model_sign_up_web import SignUpWebRequest


# ── Insertion dans login_user ─────────────────────────────────────────────────

def insert_new_user(data: SignUpWebRequest) -> str:
    """
    Crée un enregistrement dans la table login_user.
    Retourne le user_id généré (UUID).
    Lève une ValueError si l'identifiant ou l'email existe déjà.
    """

    user_id    = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    new_user = LoginUser(
        id             = user_id,
        identifiant    = data.nom_utilisateur.strip(),
        password       = data.mot_de_passe,
        email          = data.email.strip().lower(),
        date_naissance = data.date_naissance,
        created_at     = created_at,
    )

    with Session(engine) as session:
        try:
            session.add(new_user)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            err = str(e.orig).lower()
            if "identifiant" in err:
                raise ValueError("Ce nom d'utilisateur est déjà pris.")
            if "email" in err:
                raise ValueError("Cette adresse mail est déjà utilisée.")
            raise ValueError("Erreur d'intégrité en base de données.")

    return user_id

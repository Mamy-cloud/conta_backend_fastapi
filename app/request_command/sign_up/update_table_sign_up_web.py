# ================================================
# update_table_sign_up_web.py
# Insère un nouvel utilisateur dans login_user
# et retourne id, identifiant, email
# ================================================

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.connexion_db.connexion_db import engine
from app.request_command.request_create_table import LoginUser
from app.models.base_model_sign_up_web import SignUpWebRequest


@dataclass
class NewUserSession:
    user_id:     str
    identifiant: str
    email:       str


def insert_new_user(data: SignUpWebRequest) -> NewUserSession:

    user_id    = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    print("=" * 60)
    print("[DEBUG] insert_new_user() — début")
    print(f"[DEBUG] user_id généré    : {user_id}")
    print(f"[DEBUG] identifiant       : {data.nom_utilisateur.strip()}")
    print(f"[DEBUG] email             : {data.email.strip().lower()}")
    print(f"[DEBUG] date_naissance    : {data.date_naissance}")
    print(f"[DEBUG] created_at        : {created_at}")
    print("=" * 60)

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
            print("[DEBUG] Ajout de l'utilisateur en session...")
            session.add(new_user)
            session.commit()
            print("[DEBUG] ✅ Commit réussi — utilisateur inséré en DB")

        except IntegrityError as e:
            session.rollback()
            err = str(e.orig).lower()
            print(f"[DEBUG] ❌ IntegrityError : {err}")
            if "identifiant" in err:
                raise ValueError("Ce nom d'utilisateur est déjà pris.")
            if "email" in err:
                raise ValueError("Cette adresse mail est déjà utilisée.")
            raise ValueError("Erreur d'intégrité en base de données.")

        except Exception as e:
            session.rollback()
            print(f"[DEBUG] ❌ Exception inattendue en DB : {type(e).__name__} — {e}")
            raise

    result = NewUserSession(
        user_id     = user_id,
        identifiant = data.nom_utilisateur.strip(),
        email       = data.email.strip().lower(),
    )

    print("[DEBUG] NewUserSession retourné :")
    print(f"  user_id     : {result.user_id}")
    print(f"  identifiant : {result.identifiant}")
    print(f"  email       : {result.email}")
    print("=" * 60)

    return result

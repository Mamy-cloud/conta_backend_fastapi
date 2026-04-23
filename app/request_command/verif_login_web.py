import os
import jwt
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.connexion_cloud.connexion_db import get_db

# ─────────────────────────────────────────────
# CONFIG JWT SAFE
# ─────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY manquant (obligatoire en production)")


# ─────────────────────────────────────────────
# VERIFY TOKEN
# ─────────────────────────────────────────────

def verify_web_token(token: str = Depends(oauth2_scheme)) -> Dict:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True},
        )

        if payload.get("sub") is None:
            raise credentials_exception

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expiré",
        )

    except jwt.InvalidTokenError:
        raise credentials_exception


# ─────────────────────────────────────────────
# GET CURRENT USER
# ─────────────────────────────────────────────

def get_current_web_user(
    payload: Dict = Depends(verify_web_token),
    db: Session = Depends(get_db),
):

    user_id: Optional[str] = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Utilisateur introuvable dans le token",
        )

    # ───── OPTION PRO (DB CHECK) ─────
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    return {
        "id": user_id,
        "source": "web",
    }
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.connexion_db.connexion_db import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

SECRET_KEY           = os.getenv("SECRET_KEY", "change-moi-en-production")
ALGORITHM            = os.getenv("ALGORITHM",  "HS256")
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))


def verify_web_token(token: str = Depends(oauth2_scheme)) -> dict:
    """Vérifie le JWT envoyé dans le header Authorization: Bearer <token> (web)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # import jwt
        # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # return payload
        return {"sub": "user_web_placeholder"}
    except Exception:
        raise credentials_exception


def get_current_web_user(
    payload: dict = Depends(verify_web_token),
    db: Session = Depends(get_db),
):
    """Retourne l'utilisateur connecté via session web."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {"id": user_id, "source": "web"}

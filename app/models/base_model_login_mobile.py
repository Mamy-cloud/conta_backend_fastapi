from pydantic import BaseModel, field_validator
from typing import Optional


# ─────────────────────────────────────────────
# LOGIN REQUEST
# ─────────────────────────────────────────────

class LoginMobileRequest(BaseModel):
    identifiant: str
    password: str

    @field_validator("identifiant", "password", mode="before")
    @classmethod
    def not_empty(cls, v: str):
        if v is None:
            raise ValueError("Champ obligatoire")

        v = v.strip()

        if not v:
            raise ValueError("Le champ ne peut pas être vide")

        return v


# ─────────────────────────────────────────────
# SERVER STATUS
# ─────────────────────────────────────────────

class ServerStatusResponse(BaseModel):
    success: bool
    message: str


# ─────────────────────────────────────────────
# LOGIN RESPONSE
# ─────────────────────────────────────────────

class LoginMobileResponse(BaseModel):
    success: bool
    identifiant_ok: bool
    password_ok: bool
    user_id: Optional[str] = None
    message: str
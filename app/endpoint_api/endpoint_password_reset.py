# ================================================
# endpoint_password_reset.py
# POST /password/forgot — envoie email de reset
# POST /password/reset  — réinitialise le mot de passe
# Via Gmail SMTP
# ================================================

import os
import uuid
import smtplib
from email.mime.text      import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from dotenv import load_dotenv

from app.connexion_db.connexion_db import engine

load_dotenv()

GMAIL_USER         = os.getenv("GMAIL_USER",         "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
FRONTEND_URL       = os.getenv("FRONTEND_URL",       "http://localhost:5173")

router = APIRouter()


# ── Modèles ───────────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token:        str
    new_password: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _expires_at() -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()

def _is_expired(expires_at: str) -> bool:
    expiry = datetime.fromisoformat(expires_at)
    return datetime.now(timezone.utc) > expiry

def _send_email(to: str, subject: str, html: str) -> None:
    """Envoie un email via Gmail SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = to
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.sendmail(GMAIL_USER, to, msg.as_string())


# ── POST /password/forgot ─────────────────────────────────────────────────────

@router.post(
    "/password/forgot",
    summary="Demande de réinitialisation du mot de passe",
    tags=["Auth"],
)
async def forgot_password(body: ForgotPasswordRequest) -> JSONResponse:

    GENERIC_MSG = {
        "success": True,
        "message": "Si un compte correspond à cet email, un lien de réinitialisation a été envoyé.",
    }

    with engine.connect() as conn:

        # ── Cherche l'utilisateur par email ───────────
        row = conn.execute(
            text("SELECT id, email FROM login_user WHERE email = :email LIMIT 1"),
            {"email": body.email.strip().lower()},
        ).fetchone()

        if not row:
            return JSONResponse(status_code=200, content=GENERIC_MSG)

        # ── Supprime les anciens tokens ───────────────
        conn.execute(
            text("DELETE FROM password_reset_tokens WHERE user_id = :uid"),
            {"uid": row.id},
        )

        # ── Crée un nouveau token ─────────────────────
        token      = str(uuid.uuid4())
        expires_at = _expires_at()

        conn.execute(
            text("""
                INSERT INTO password_reset_tokens (id, user_id, token, expires_at, used, created_at)
                VALUES (:id, :user_id, :token, :expires_at, 0, :created_at)
            """),
            {
                "id":         str(uuid.uuid4()),
                "user_id":    row.id,
                "token":      token,
                "expires_at": expires_at,
                "created_at": _now(),
            },
        )
        conn.commit()

    # ── Envoie l'email via Gmail SMTP ─────────────────
    reset_link = f"{FRONTEND_URL}/reinitialiser-mot-de-passe?token={token}"

    try:
        _send_email(
            to      = body.email.strip().lower(),
            subject = "Réinitialisation de votre mot de passe — Conta",
            html    = f"""
                <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
                    <h2 style="color: #111; margin-bottom: 8px;">Réinitialisation du mot de passe</h2>
                    <p style="color: #555; line-height: 1.6;">
                        Vous avez demandé à réinitialiser votre mot de passe.
                        Cliquez sur le bouton ci-dessous pour choisir un nouveau mot de passe.
                    </p>
                    <a href="{reset_link}"
                       style="display: inline-block; margin: 24px 0; padding: 12px 28px;
                              background: #3ecf8e; color: #fff; border-radius: 8px;
                              text-decoration: none; font-weight: 600; font-size: 15px;">
                        Réinitialiser mon mot de passe
                    </a>
                    <p style="color: #999; font-size: 13px;">
                        Ce lien expire dans <strong>15 minutes</strong>.
                        Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
                    </p>
                </div>
            """,
        )
        print(f"[RESET] ✅ Email envoyé à {body.email}")
    except Exception as e:
        print(f"[RESET] ❌ Erreur envoi email : {e}")

    return JSONResponse(status_code=200, content=GENERIC_MSG)


# ── POST /password/reset ──────────────────────────────────────────────────────

@router.post(
    "/password/reset",
    summary="Réinitialise le mot de passe avec le token",
    tags=["Auth"],
)
async def reset_password(body: ResetPasswordRequest) -> JSONResponse:

    if not body.new_password or len(body.new_password) < 6:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Le mot de passe doit faire au moins 6 caractères."},
        )

    with engine.connect() as conn:

        row = conn.execute(
            text("""
                SELECT id, user_id, expires_at, used
                FROM password_reset_tokens
                WHERE token = :token
                LIMIT 1
            """),
            {"token": body.token},
        ).fetchone()

        if not row:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Lien invalide ou expiré."},
            )

        if row.used:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Ce lien a déjà été utilisé."},
            )

        if _is_expired(row.expires_at):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Ce lien a expiré. Faites une nouvelle demande."},
            )

        # ── Met à jour le mot de passe ─────────────────
        conn.execute(
            text("UPDATE login_user SET password = :pwd WHERE id = :uid"),
            {"pwd": body.new_password, "uid": row.user_id},
        )

        # ── Invalide le token ──────────────────────────
        conn.execute(
            text("UPDATE password_reset_tokens SET used = 1 WHERE id = :id"),
            {"id": row.id},
        )

        conn.commit()

    return JSONResponse(
        status_code=200,
        content={"success": True, "message": "Mot de passe mis à jour avec succès."},
    )

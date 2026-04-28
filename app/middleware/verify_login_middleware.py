# ================================================
# verify_login_middleware.py
# Middleware FastAPI — vérifie les cookies de session
# Si manquants → redirige vers /error_404
# ================================================

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ── Routes publiques — pas de vérification ────────────────────────────────────
PUBLIC_ROUTES = {
    "/login/web",
    "/sign_up/web",
    "/logout/web/conta",
    "/error_404",
    "/password/forgot",   # ← ajouter
    "/password/reset",    # ← ajouter
    "/",
}

# ── Préfixes publics ──────────────────────────────────────────────────────────
PUBLIC_PREFIXES = (
    "/docs",
    "/openapi",
    "/redoc",
    "/favicon",
    "/mobile/",
)

# ── Cookies requis — seulement les essentiels ─────────────────────────────────
REQUIRED_COOKIES = (
    "session_user_id",
    "session_identifiant",
)


class VerifyLoginMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        path = request.url.path

        # ── Ignore les routes publiques ───────────────
        if path in PUBLIC_ROUTES:
            return await call_next(request)

        # ── Ignore les préfixes publics ───────────────
        if path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        # ── Vérifie les cookies requis ────────────────
        missing = [
            cookie for cookie in REQUIRED_COOKIES
            if not request.cookies.get(cookie)
        ]

        if missing:
            print(f"[MIDDLEWARE] ❌ Cookies manquants : {missing} — path={path}")
            return JSONResponse(
                status_code=401,
                content={
                    "success":  False,
                    "message":  "Non connecté.",
                    "redirect": "/error_404",
                },
            )

        return await call_next(request)

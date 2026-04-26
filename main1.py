from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.endpoint_api.mobile_transfert_cloud  import router as mobile_transfert_router
from app.endpoint_api.endpoint_login_mobile   import router as login_router
from app.endpoint_api.endpoint_sign_up_web    import router as sign_up_web_router
from app.endpoint_api.endpoint_login_web      import router as login_web_router
from app.endpoint_api.endpoint_logout_web     import router as logout_web_router

app = FastAPI(
    title       = "Conta Backend API",
    description = "API FastAPI avec support CORS pour web et mobile",
    version     = "1.0.0"
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:5173",        # Vite dev server
    "http://localhost:8000",        # Swagger UI
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "https://ton-app.vercel.app",   # ← remplace par ton URL Vercel
]

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ─── Routes de base ───────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {"message": "API opérationnelle ✅"}

@app.get("/health", tags=["Root"])
async def health_check():
    return {"status": "ok"}

@app.get("/bonjour/uptime_robot")
def bonjour_uptime_robot():
    return {
        "message": "Bonjour Uptime Robot 👋",
        "status":  "ok",
    }

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(mobile_transfert_router)
app.include_router(login_router)
app.include_router(sign_up_web_router)
app.include_router(login_web_router)
app.include_router(logout_web_router)

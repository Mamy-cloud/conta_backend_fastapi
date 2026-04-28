from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

from app.endpoint_api.mobile_transfert_cloud   import router as mobile_transfert_router
from app.endpoint_api.endpoint_login_mobile    import router as login_router
from app.endpoint_api.endpoint_sign_up_web     import router as sign_up_web_router
from app.endpoint_api.endpoint_login_web       import router as login_web_router
from app.endpoint_api.endpoint_logout_web      import router as logout_web_router
from app.endpoint_api.endpoint_get_session_web import router as session_cookie_router
from app.endpoint_api.endpoint_display_info_temoin import router as display_info_temoin_router
from app.endpoint_api.endpoint_transcriptor import router as transcriptor_router
from app.endpoint_api.endpoint_list_of_interviewer_server import router as list_login_of_interviwer
from app.endpoint_api.endpoint_list_of_data_collected import router as list_data_collected_router
from app.middleware.verify_login_middleware import VerifyLoginMiddleware
from app.endpoint_api.endpoint_password_reset import router as password_reset_router

from app.cron.cron_create_tables import start_scheduler, job_check_tables


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Démarrage ─────────────────────────────────────
    print("[STARTUP] Création / vérification des tables...")
    job_check_tables()      # création immédiate au lancement
    start_scheduler()       # puis toutes les 3 minutes
    print("[STARTUP] ✅ Serveur prêt.")

    yield

    # ── Arrêt ─────────────────────────────────────────
    print("[SHUTDOWN] Arrêt du scheduler.")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Conta Backend API",
    description = "API FastAPI avec support CORS pour web et mobile",
    version     = "1.0.0",
    lifespan    = lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:5173",                                    # Vite dev server
    "http://localhost:8000",                                    # Swagger UI
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "https://react-web-transcriptor-conta.vercel.app",
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
app.include_router(session_cookie_router)
app.include_router(display_info_temoin_router)
app.include_router(transcriptor_router)
app.include_router(list_login_of_interviwer)
app.include_router(list_data_collected_router)
app.add_middleware(VerifyLoginMiddleware)
app.include_router(password_reset_router)

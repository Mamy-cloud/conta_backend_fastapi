from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.endpoint_api.mobile_transfert_cloud import router as mobile_transfert_router
from app.endpoint_api.endpoint_login_mobile import router as login_router

app = FastAPI(
    title="Conta Backend API",
    description="API FastAPI avec support CORS pour web et mobile",
    version="1.0.0"
)

# ─── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # ⚠️  Remplace par tes domaines en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(mobile_transfert_router)

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
        "status": "ok",
        
    }

app.include_router(login_router)


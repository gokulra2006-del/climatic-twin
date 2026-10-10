import os
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.api_v1.api import api_router
from app.api.deps import get_db, get_db_optional
from app.core.mqtt import start_mqtt_client
from app.db.session import SessionLocal
from app.models.user import User
from app.core import security

logger = logging.getLogger(__name__)

# Keep a reference to the MQTT client
mqtt_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_client
    
    # Seed demo users if they don't exist
    try:
        db = SessionLocal()
        if not db.query(User).first():
            # Passwords MUST be set via environment variables — no insecure defaults
            admin_pw = os.getenv("DEMO_ADMIN_PASSWORD")
            operator_pw = os.getenv("DEMO_OPERATOR_PASSWORD")
            viewer_pw = os.getenv("DEMO_VIEWER_PASSWORD")
            if admin_pw and operator_pw and viewer_pw:
                demo_users = [
                    User(username="admin", email="admin@climatetwin.local", role="admin", hashed_password=security.get_password_hash(admin_pw)),
                    User(username="operator", email="operator@climatetwin.local", role="operator", hashed_password=security.get_password_hash(operator_pw)),
                    User(username="viewer", email="viewer@climatetwin.local", role="viewer", hashed_password=security.get_password_hash(viewer_pw)),
                ]
                db.add_all(demo_users)
                db.commit()
                logger.info("Demo users seeded successfully.")
            else:
                logger.warning(
                    "Demo user passwords not set in environment. "
                    "Set DEMO_ADMIN_PASSWORD, DEMO_OPERATOR_PASSWORD, DEMO_VIEWER_PASSWORD to seed users."
                )
        db.close()
    except Exception as e:
        logger.info(f"User seed skipped (DB offline): {e}")

    # MQTT is optional — gracefully degrade if broker is unavailable
    try:
        mqtt_client = start_mqtt_client(broker_url="localhost", port=1883)
        logger.info("MQTT client connected.")
    except Exception as e:
        logger.warning(f"MQTT broker unavailable — running without real-time sensor ingestion: {e}")
        mqtt_client = None
    yield
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Digital Twin Framework for Climate Hazard Monitoring Backend",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.API_V1_STR)
@app.get("/")
def read_root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} backend service.",
        "docs_url": "/docs" if settings.DEBUG else None
    }

@app.get("/health")
def health_check():
    from app.db.session import is_db_connected
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database_connected": is_db_connected(),
        "mqtt_connected": mqtt_client is not None,
        "debug_mode": settings.DEBUG
    }



# Trigger reload

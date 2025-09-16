from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from db import models
from core.config import settings
from db.connection import engine, SessionLocal
from api.tweet import router as tweet_router
from api.auth import router as auth_router
from security.Oauth import get_current_user

# FastAPI app initialization
app = FastAPI(
    title=settings.APP_NAME,
)

# CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

models.Base.metadata.create_all(bind=engine)


# Register routers
app.include_router(auth_router)
app.include_router(tweet_router)
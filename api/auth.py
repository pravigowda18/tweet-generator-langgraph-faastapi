from fastapi import  Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from schemas import user
from db.connection import get_db
from db import models
from security.hashing import Hasher
from security.JWTtoken import create_access_token
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from core.config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(
    prefix="/auth",
    tags=['Auth']
)


def create_user(db: Session, user: user.UserCreate):
    hashed_password = Hasher.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/register", response_model=user.UserShow, status_code=status.HTTP_201_CREATED)
def register(user: user.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        models.User.email == user.email
        ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    new_user = create_user(db, user)
    return new_user

@router.get('/users/{id}', response_model=user.UserShow)
def get_user(id: str, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.user_id == id)
    user = user_query.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'User with id {id} not available')
        
    return user


@router.post("/token", response_model=user.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.email == form_data.username
        ).first()
    
    if not user or not Hasher.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
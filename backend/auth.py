from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import User, RefreshToken
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

SECRET_KEY = os.getenv("SECRET_KEY")  # Replace with your secret key
REFRESH_SECRET_KEY=os.getenv("REFRESH_SECRET_KEY")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class CreateUserRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, 
                      create_user_request: CreateUserRequest):
    if db.query(User).filter(User.username == create_user_request.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username already registered")
    create_user_model = User(
        username=create_user_request.username,
        hashed_password=pwd_context.hash(create_user_request.password),
    )
    db.add(create_user_model)
    db.commit()

def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, expires_delta: timedelta | None = None):
    encode = {"sub": username, "id": user_id}
    if expires_delta:
        expires = datetime.now(timezone.utc) + expires_delta
    else:
        expires = datetime.now(timezone.utc) + timedelta(minutes=20)
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(username: str, user_id: int, expires_delta: timedelta | None = None):
    encode = {"sub": username, "id": user_id}
    if expires_delta:
        expires = datetime.now(timezone.utc) + expires_delta
    else:
        expires = datetime.now(timezone.utc) + timedelta(days=7)
    encode.update({"exp": expires})
    return jwt.encode(encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.username, user.id, timedelta(15))
    refresh_token = create_refresh_token(user.username, user.id, timedelta(minutes=60*24*14))
    refresh_exp = datetime.now(timezone.utc) + timedelta(minutes=60*24*14)
    db.add(RefreshToken(
        user_id=user.id, 
        token=refresh_token, 
        expires_at=refresh_exp,
        revoked=False))
    db.commit()
    return {"access_token": token, "refresh_token" : refresh_token, "token_type": "bearer"}

@router.get("/verify-token")
async def get_current_user_refresh(request: Request, db: db_dependency) -> dict:
    # 1. Get token from Authorization header
    auth: str = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(auth)

    if not token or scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    try:
        # 2. Try decoding access token (might be expired)
        payloaded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payloaded.get("sub")
        user_id: int = payloaded.get("id")
        token_expired = False
    except JWTError as e:   
        # 3. Try decoding without expiration check (to extract user info)
        try:
            payloaded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
            username: str = payloaded.get("sub")
            user_id: int = payloaded.get("id")
            token_expired = True
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        
    # 4. Check if refresh token exists for this user    
    refresh_entry = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc).timestamp()
        ).first()

    if not refresh_entry:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")

    # 5. If token was expired, issue a new one
    if token_expired:
        new_access_token = create_access_token(username, user_id, timedelta(minutes=15))
        return {"username": username, "id": user_id, "new_access_token": new_access_token}
    
    return {"username": username, "id": user_id}
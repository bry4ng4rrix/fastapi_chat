from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlmodel import Session, select
from sqlalchemy.sql import exists
from passlib.context import CryptContext
from database import get_session
from models import User, UserCreate, UserRead, TokenBlacklist

router = APIRouter(tags=["auth"])

SECRET_KEY = "bryangarrix"  # Change to a secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(email: str, session: Session):
    return session.exec(select(User).where(User.email == email)).first()

def authenticate_user(email: str, password: str, session: Session):
    user = get_user_by_email(email, session)
    if not user or not verify_password(password, user.password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "sub": str(data["user_id"])})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def is_token_blacklisted(token: str, session: Session) -> bool:
    """Vérifier si un token est dans la blacklist"""
    blacklisted = session.exec(
        select(TokenBlacklist).where(TokenBlacklist.token == token)
    ).first()
    return blacklisted is not None

async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    """Récupérer l'utilisateur actuel avec vérification de blacklist"""
    try:
        # Vérifier si le token est blacklisté
        if is_token_blacklisted(token, session):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token has been revoked"
            )
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token"
        )
    
    user = session.get(User, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found"
        )
    return user

async def get_user_from_token(token: str, session: Session) -> User:
    """
    Authentifie un utilisateur à partir d'un token JWT pour WebSocket
    Retourne None si le token est invalide ou blacklisté
    """
    try:
        # Vérifier si le token est blacklisté
        if is_token_blacklisted(token, session):
            return None
        
        # Décoder le token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        # Récupérer l'utilisateur
        user = session.get(User, int(user_id))
        return user
        
    except JWTError:
        return None

@router.post("/register", response_model=UserRead)
async def register_user(user: UserCreate, session: Session = Depends(get_session)):
    email_exists = session.exec(select(exists().where(User.email == user.email))).first()
    if email_exists:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = pwd_context.hash(user.password)
    db_user = User(name=user.name, email=user.email, password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"user_id": user.id}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    """Déconnexion - ajouter le token à la blacklist"""
    try:
        # Vérifier que le token est valide avant de le blacklister
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Ajouter le token à la blacklist
        blacklisted_token = TokenBlacklist(
            token=token,
            blacklisted_at=datetime.utcnow()
        )
        session.add(blacklisted_token)
        session.commit()
        
        return {"message": "Successfully logged out"}
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token"
        )

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Récupérer les informations de l'utilisateur connecté"""
    return current_user

@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Rafraîchir le token d'accès"""
    access_token = create_access_token(
        data={"user_id": current_user.id}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}
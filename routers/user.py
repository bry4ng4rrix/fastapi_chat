from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlmodel import Session, select
from database import get_session
from models import User, UserCreate, UserRead
from routers.auth import get_current_user
router = APIRouter( prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    email = session.exec(select(User).where(User.email == user.email)).first()
    if email:
        raise HTTPException(status_code=400, detail="Email deja exister ")
    db_user = User.from_orm(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserRead])
def read_users(session: Session = Depends(get_session) , curent_user: User = Depends(get_current_user)):
    users = session.exec(select(User)).all()
    return users

@router.get("/me", response_model=UserRead)
def read_current_user(curent_user: User = Depends(get_current_user)):
    return curent_user

@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
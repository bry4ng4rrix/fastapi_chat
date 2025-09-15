from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlmodel import Session, select
from database import get_session
from models import Message, MessageCreate, MessageRead, User
from routers.auth import get_current_user



router = APIRouter()


@router.post("/", response_model=MessageRead)
def create_message(message: MessageCreate, session: Session = Depends(get_session) , curent_user: User = Depends(get_current_user)):
    user = session.get(User, message.user_id)
    db_message = Message(
        user_id=curent_user.id,
        message=message.message,
        date_create = message.date_create
    )
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    return db_message


@router.get("/", response_model=List[MessageRead])
def read_messages(session: Session = Depends(get_session) ,curent_user: User = Depends(get_current_user)):
    messages = session.exec(select(Message)).all()
    return messages




@router.get("/{user_id}", response_model=List[MessageRead])
def read_user_messages(user_id: int, session: Session = Depends(get_session) , curent_user: User = Depends(get_current_user)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    messages = session.exec(select(Message).where(Message.user_id == user_id)).all()
    return messages

@router.put("/{message_id}", response_model=MessageRead)
def update_message(message_id: int, message: MessageCreate, session: Session = Depends(get_session), curent_user: User = Depends(get_current_user)):
    db_message = session.get(Message, message_id)
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")
    if db_message.user_id != curent_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this message")
    db_message.message = message.message
    db_message.date_create = message.date_create
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    return db_message
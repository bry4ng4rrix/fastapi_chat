from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from models import Message, User
from database import get_session
from routers.auth import get_current_user

router = APIRouter(
    tags=["messages"]
)

# --- Envoyer un message ---
@router.post("/", response_model=Message)
def send_message(
    receiver_id: int,
    content: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    receiver = session.get(User, receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Utilisateur destinataire non trouvé")

    message = Message(
        content=content,
        sender_id=current_user.id,
        receiver_id=receiver_id
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message

# --- Récupérer les messages de l'utilisateur connecté ---
@router.get("/", response_model=List[Message])
def get_my_messages(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    messages = session.exec(
        select(Message).where(
            (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
        )
    ).all()
    return messages

# --- Récupérer la conversation avec un autre utilisateur ---
@router.get("/conversation/{user_id}", response_model=List[Message])
def get_conversation(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    other_user = session.get(User, user_id)
    if not other_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    messages = session.exec(
        select(Message).where(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
        )
    ).all()
    return messages

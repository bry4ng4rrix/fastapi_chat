from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlmodel import Session, select
from typing import List, Dict
from models import Message, User
from database import get_session
from routers.auth import get_current_user, get_user_from_token
import json
from datetime import datetime

router = APIRouter(
    tags=["messages"]
)

# Gestionnaire de connexions WebSocket
class ConnectionManager:
    def __init__(self):
        # Dictionnaire pour stocker les connexions WebSocket par user_id
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"Utilisateur {user_id} connecté via WebSocket")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"Utilisateur {user_id} déconnecté du WebSocket")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            disconnected_websockets = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    # Connexion fermée, marquer pour suppression
                    disconnected_websockets.append(websocket)
            
            # Nettoyer les connexions fermées
            for ws in disconnected_websockets:
                self.disconnect(ws, user_id)

    async def send_message_to_conversation(self, message: dict, sender_id: int, receiver_id: int):
        # Envoyer le message au sender et au receiver
        await self.send_personal_message(message, sender_id)
        await self.send_personal_message(message, receiver_id)

# Instance globale du gestionnaire de connexions
manager = ConnectionManager()

# --- WebSocket endpoint ---
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    session: Session = Depends(get_session)
):
    try:
        # Authentifier l'utilisateur via le token
        current_user = await get_user_from_token(token, session)
        if not current_user:
            await websocket.close(code=4001, reason="Token invalide")
            return

        # Connecter l'utilisateur
        await manager.connect(websocket, current_user.id)

        try:
            while True:
                # Écouter les messages du client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Traitement des différents types de messages
                if message_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
                elif message_data.get("type") == "send_message":
                    # Envoyer un message via WebSocket
                    receiver_id = message_data.get("receiver_id")
                    content = message_data.get("content")
                    
                    if not receiver_id or not content:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "receiver_id et content requis"
                        }))
                        continue
                    
                    # Vérifier que le destinataire existe
                    receiver = session.get(User, receiver_id)
                    if not receiver:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Utilisateur destinataire non trouvé"
                        }))
                        continue
                    
                    # Créer le message en base
                    message = Message(
                        content=content,
                        sender_id=current_user.id,
                        receiver_id=receiver_id
                    )
                    session.add(message)
                    session.commit()
                    session.refresh(message)
                    
                    # Diffuser le message via WebSocket
                    message_dict = {
                        "type": "new_message",
                        "id": message.id,
                        "content": message.content,
                        "sender_id": message.sender_id,
                        "receiver_id": message.receiver_id,
                        "created_at": message.created_at.isoformat() if message.created_at else None
                    }
                    
                    await manager.send_message_to_conversation(
                        message_dict, current_user.id, receiver_id
                    )

        except WebSocketDisconnect:
            manager.disconnect(websocket, current_user.id)
            
    except Exception as e:
        print(f"Erreur WebSocket: {e}")
        await websocket.close(code=4000, reason="Erreur serveur")

# --- Envoyer un message (HTTP) ---
@router.post("/", response_model=Message)
async def send_message(
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
    
    # Diffuser le message via WebSocket
    message_dict = {
        "type": "new_message",
        "id": message.id,
        "content": message.content,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "created_at": message.created_at.isoformat() if message.created_at else None
    }
    
    await manager.send_message_to_conversation(
        message_dict, current_user.id, receiver_id
    )
    
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
        ).order_by(Message.created_at)
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
        ).order_by(Message.created_at)
    ).all()
    return messages

# --- Update message ---
@router.put("/{message_id}", response_model=Message)
async def update_message(
    message_id: int,
    content: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    message = session.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message non trouvé")
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à modifier ce message")
    
    message.content = content
    session.add(message)
    session.commit()
    session.refresh(message)
    
    # Diffuser la mise à jour via WebSocket
    update_dict = {
        "type": "message_updated",
        "id": message.id,
        "content": message.content,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "updated_at": datetime.now().isoformat()
    }
    
    await manager.send_message_to_conversation(
        update_dict, message.sender_id, message.receiver_id
    )
    
    return message

# --- Supprimer un message ---
@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    message = session.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message non trouvé")
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à supprimer ce message")
    
    receiver_id = message.receiver_id
    
    session.delete(message)
    session.commit()
    
    # Diffuser la suppression via WebSocket
    delete_dict = {
        "type": "message_deleted",
        "id": message_id,
        "sender_id": current_user.id,
        "receiver_id": receiver_id
    }
    
    await manager.send_message_to_conversation(
        delete_dict, current_user.id, receiver_id
    )
    
    return {"message": "Message supprimé avec succès"}

# --- Obtenir la liste des utilisateurs connectés ---
@router.get("/online-users", response_model=List[int])
def get_online_users(current_user: User = Depends(get_current_user)):
    return list(manager.active_connections.keys())
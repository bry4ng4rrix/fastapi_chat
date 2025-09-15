from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
from sqlmodel import Session, select
from datetime import datetime, timedelta
import json
import asyncio
from database import get_session
from models import User, UserCreate, UserRead
from routers.auth import get_current_user, get_user_from_token

# Store des connexions WebSocket actives
class ConnectionManager:
    def __init__(self):
        # Dictionnaire : user_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Dictionnaire pour stocker la dernière activité : user_id -> datetime
        self.last_activity: Dict[int, datetime] = {}
        # Seuil d'inactivité en secondes (par exemple 5 minutes)
        self.inactivity_threshold = 300

    async def connect(self, websocket: WebSocket, user_id: int):
        """Connecte un utilisateur via WebSocket"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.last_activity[user_id] = datetime.now()
        
        # Notifier tous les autres utilisateurs que cet utilisateur est maintenant actif
        await self.broadcast_user_status(user_id, "online")

    async def disconnect(self, websocket: WebSocket, user_id: int):
        """Déconnecte un utilisateur"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Si plus aucune connexion active pour cet utilisateur
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.last_activity:
                    del self.last_activity[user_id]
                
                # Notifier que l'utilisateur est offline
                await self.broadcast_user_status(user_id, "offline")

    async def update_activity(self, user_id: int):
        """Met à jour la dernière activité d'un utilisateur"""
        if user_id in self.active_connections:
            self.last_activity[user_id] = datetime.now()

    def is_user_active(self, user_id: int) -> bool:
        """Vérifie si un utilisateur est actif"""
        if user_id not in self.active_connections:
            return False
        
        if user_id not in self.last_activity:
            return False
        
        time_since_activity = datetime.now() - self.last_activity[user_id]
        return time_since_activity.total_seconds() < self.inactivity_threshold

    def get_active_users(self) -> List[int]:
        """Retourne la liste des utilisateurs actifs"""
        active_users = []
        current_time = datetime.now()
        
        for user_id, last_activity in self.last_activity.items():
            if user_id in self.active_connections:
                time_since_activity = current_time - last_activity
                if time_since_activity.total_seconds() < self.inactivity_threshold:
                    active_users.append(user_id)
        
        return active_users

    async def send_personal_message(self, message: str, user_id: int):
        """Envoie un message à un utilisateur spécifique"""
        if user_id in self.active_connections:
            disconnected_websockets = set()
            
            for websocket in self.active_connections[user_id].copy():
                try:
                    await websocket.send_text(message)
                except:
                    disconnected_websockets.add(websocket)
            
            # Nettoyer les connexions fermées
            for ws in disconnected_websockets:
                self.active_connections[user_id].discard(ws)

    async def broadcast_user_status(self, user_id: int, status: str):
        """Diffuse le statut d'un utilisateur à tous les autres utilisateurs connectés"""
        message = json.dumps({
            "type": "user_status",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
        # Envoyer à tous les utilisateurs connectés sauf l'utilisateur concerné
        for connected_user_id, websockets in self.active_connections.items():
            if connected_user_id != user_id:
                disconnected_websockets = set()
                
                for websocket in websockets.copy():
                    try:
                        await websocket.send_text(message)
                    except:
                        disconnected_websockets.add(websocket)
                
                # Nettoyer les connexions fermées
                for ws in disconnected_websockets:
                    websockets.discard(ws)

    async def broadcast_to_all(self, message: str):
        """Diffuse un message à tous les utilisateurs connectés"""
        for user_id, websockets in self.active_connections.items():
            disconnected_websockets = set()
            
            for websocket in websockets.copy():
                try:
                    await websocket.send_text(message)
                except:
                    disconnected_websockets.add(websocket)
            
            # Nettoyer les connexions fermées
            for ws in disconnected_websockets:
                websockets.discard(ws)

# Instance globale du gestionnaire de connexions
manager = ConnectionManager()

router = APIRouter(tags=["Utilisateurs"])

# Routes WebSocket
@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """Point d'entrée WebSocket pour la gestion d'activité des utilisateurs"""
    user = None
    try:
        # Créer une session pour la vérification du token
        from database import engine
        with Session(engine) as session:
            # Vérifier le token et récupérer l'utilisateur
            user = get_user_from_token(token, session)
            if not user:
                await websocket.close(code=4001)
                return
        
        await manager.connect(websocket, user.id)
        
        # Envoyer la liste des utilisateurs actifs au nouvel utilisateur connecté
        active_users = manager.get_active_users()
        await websocket.send_text(json.dumps({
            "type": "active_users",
            "users": active_users,
            "timestamp": datetime.now().isoformat()
        }))
        
        try:
            while True:
                # Recevoir des messages du client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Mettre à jour l'activité de l'utilisateur
                await manager.update_activity(user.id)
                
                # Traiter différents types de messages
                if message_data.get("type") == "ping":
                    # Simple ping pour maintenir la connexion active
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                elif message_data.get("type") == "get_active_users":
                    # Demande de la liste des utilisateurs actifs
                    active_users = manager.get_active_users()
                    await websocket.send_text(json.dumps({
                        "type": "active_users",
                        "users": active_users,
                        "timestamp": datetime.now().isoformat()
                    }))
                
                elif message_data.get("type") == "activity_update":
                    # Simple mise à jour d'activité
                    await manager.update_activity(user.id)
        
        except WebSocketDisconnect:
            if user:
                await manager.disconnect(websocket, user.id)
    
    except Exception as e:
        print(f"Erreur WebSocket: {e}")
        if user:
            await manager.disconnect(websocket, user.id)
        await websocket.close(code=4000)

# Routes REST existantes - CORRIGÉES
@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # Vérifier si l'email existe déjà
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email déjà existant")
    
    # Créer le nouvel utilisateur (corriger from_orm qui n'existe plus dans SQLModel récent)
    db_user = User(
        name=user.name,
        email=user.email,
        password=user.password  # Assurez-vous de hasher le mot de passe si nécessaire
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserRead])
def read_users(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    users = session.exec(select(User)).all()
    return users

@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserRead)
def update_current_user(user: UserCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_user = session.get(User, current_user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    user_data = user.dict(exclude_unset=True)
    for key, value in user_data.items():
        setattr(db_user, key, value)
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user

# Nouvelles routes pour la gestion d'activité
@router.get("/active/list")
async def get_active_users(current_user: User = Depends(get_current_user)):
    """Retourne la liste des utilisateurs actuellement actifs"""
    active_user_ids = manager.get_active_users()
    return {
        "active_users": active_user_ids,
        "count": len(active_user_ids),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/active/status/{user_id}")
async def check_user_activity(user_id: int, current_user: User = Depends(get_current_user)):
    """Vérifie si un utilisateur spécifique est actif"""
    is_active = manager.is_user_active(user_id)
    return {
        "user_id": user_id,
        "is_active": is_active,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/broadcast")
async def broadcast_message(message: dict, current_user: User = Depends(get_current_user)):
    """Diffuse un message à tous les utilisateurs connectés"""
    broadcast_data = {
        "type": "broadcast",
        "from_user": current_user.name,
        "message": message.get("message", ""),
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_to_all(json.dumps(broadcast_data))
    return {"status": "Message diffusé", "recipients": len(manager.active_connections)}

# Tâche en arrière-plan pour nettoyer les connexions inactives
async def cleanup_inactive_connections():
    """Nettoie périodiquement les connexions inactives"""
    while True:
        await asyncio.sleep(60)  # Vérifie toutes les minutes
        
        current_time = datetime.now()
        inactive_users = []
        
        for user_id, last_activity in manager.last_activity.items():
            time_since_activity = current_time - last_activity
            if time_since_activity.total_seconds() > manager.inactivity_threshold:
                inactive_users.append(user_id)
        
        # Marquer les utilisateurs inactifs comme offline
        for user_id in inactive_users:
            await manager.broadcast_user_status(user_id, "inactive")
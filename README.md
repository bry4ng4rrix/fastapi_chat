# API de Messagerie en Temps Réel

Une API FastAPI complète pour un système de messagerie en temps réel avec WebSocket et authentification JWT.

## 📋 Fonctionnalités

- 💬 **Messagerie en temps réel** avec WebSocket
- 🔐 **Authentification JWT** sécurisée
- 👥 **Gestion des utilisateurs** avec CRUD complet
- 📨 **Conversations privées** entre utilisateurs
- ✏️ **Modification et suppression** de messages
- 🟢 **Statut en ligne** des utilisateurs connectés
- 🚫 **Blacklist de tokens** pour la déconnexion sécurisée

## 🏗️ Architecture

### Modèles de Données

#### User (Utilisateur)
```python
class User(SQLModel, table=True):
    id: Optional[int]           # Clé primaire
    name: str                   # Nom (max 50 caractères)
    email: str                  # Email unique (max 100 caractères)
    password: str               # Mot de passe hashé (max 100 caractères)
    messages_sent: List[Message]    # Messages envoyés
    messages_received: List[Message] # Messages reçus
```

#### Message (Message)
```python
class Message(SQLModel, table=True):
    id: Optional[int]           # Clé primaire
    content: str                # Contenu du message
    timestamp: datetime         # Horodatage (UTC)
    sender_id: int              # ID de l'expéditeur
    receiver_id: int            # ID du destinataire
    sender: Optional[User]      # Relation vers l'expéditeur
    receiver: Optional[User]    # Relation vers le destinataire
```

#### TokenBlacklist (Blacklist de Tokens)
```python
class TokenBlacklist(SQLModel, table=True):
    id: Optional[int]           # Clé primaire
    token: str                  # Token JWT blacklisté
    blacklisted_at: datetime    # Date de blacklistage
```

## 🚀 Endpoints API

### Authentification
Les endpoints nécessitent une authentification JWT via header `Authorization: Bearer <token>`

### Messages HTTP

#### `POST /messages/`
Envoie un nouveau message
```json
{
  "receiver_id": 2,
  "content": "Bonjour, comment allez-vous ?"
}
```

#### `GET /messages/`
Récupère tous les messages de l'utilisateur connecté

#### `GET /messages/conversation/{user_id}`
Récupère la conversation avec un utilisateur spécifique

#### `PUT /messages/{message_id}`
Modifie le contenu d'un message (propriétaire uniquement)
```json
{
  "content": "Message modifié"
}
```

#### `DELETE /messages/{message_id}`
Supprime un message (propriétaire uniquement)

#### `GET /messages/online-users`
Retourne la liste des IDs des utilisateurs actuellement connectés

## 🔌 WebSocket

### Connexion
```
ws://localhost:8000/messages/ws?token=<jwt_token>
```

### Messages WebSocket

#### Ping/Pong
```json
// Client → Serveur
{"type": "ping"}

// Serveur → Client
{"type": "pong"}
```

#### Envoyer un message
```json
// Client → Serveur
{
  "type": "send_message",
  "receiver_id": 2,
  "content": "Message via WebSocket"
}
```

#### Événements reçus du serveur

**Nouveau message :**
```json
{
  "type": "new_message",
  "id": 123,
  "content": "Contenu du message",
  "sender_id": 1,
  "receiver_id": 2,
  "created_at": "2025-09-15T10:30:00"
}
```

**Message modifié :**
```json
{
  "type": "message_updated",
  "id": 123,
  "content": "Nouveau contenu",
  "sender_id": 1,
  "receiver_id": 2,
  "updated_at": "2025-09-15T10:35:00"
}
```

**Message supprimé :**
```json
{
  "type": "message_deleted",
  "id": 123,
  "sender_id": 1,
  "receiver_id": 2
}
```

**Erreur :**
```json
{
  "type": "error",
  "message": "Description de l'erreur"
}
```

## ⚙️ Gestionnaire de Connexions

La classe `ConnectionManager` gère les connexions WebSocket :

- **Connexions multiples** par utilisateur supportées
- **Nettoyage automatique** des connexions fermées
- **Diffusion ciblée** des messages aux participants de la conversation
- **Gestion des erreurs** et reconnexions

### Fonctionnalités du ConnectionManager

- `connect(websocket, user_id)` : Enregistre une nouvelle connexion
- `disconnect(websocket, user_id)` : Supprime une connexion
- `send_personal_message(message, user_id)` : Envoie à un utilisateur spécifique
- `send_message_to_conversation(message, sender_id, receiver_id)` : Diffuse aux participants

## 🔧 Configuration Technique

### Dépendances principales
- **FastAPI** : Framework web moderne
- **SQLModel** : ORM basé sur SQLAlchemy et Pydantic
- **WebSocket** : Communication temps réel
- **JWT** : Authentification par tokens

### Structure de base de données
- Relations **many-to-one** entre Message et User
- Index sur les tokens blacklistés pour les performances
- Horodatage automatique avec `datetime.utcnow`

## 📝 Exemples d'utilisation

### Client JavaScript WebSocket
```javascript
const ws = new WebSocket(`ws://localhost:8000/messages/ws?token=${jwt_token}`);

ws.onopen = () => {
    console.log('Connecté au WebSocket');
    // Ping périodique
    setInterval(() => {
        ws.send(JSON.stringify({type: 'ping'}));
    }, 30000);
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch(data.type) {
        case 'new_message':
            displayMessage(data);
            break;
        case 'message_updated':
            updateMessage(data);
            break;
        case 'message_deleted':
            removeMessage(data.id);
            break;
    }
};

// Envoyer un message
function sendMessage(receiverId, content) {
    ws.send(JSON.stringify({
        type: 'send_message',
        receiver_id: receiverId,
        content: content
    }));
}
```

### Client HTTP avec fetch
```javascript
// Envoyer un message via HTTP
async function sendMessageHTTP(receiverId, content) {
    const response = await fetch('/messages/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': `Bearer ${jwt_token}`
        },
        body: new URLSearchParams({
            receiver_id: receiverId,
            content: content
        })
    });
    return response.json();
}

// Récupérer une conversation
async function getConversation(userId) {
    const response = await fetch(`/messages/conversation/${userId}`, {
        headers: {
            'Authorization': `Bearer ${jwt_token}`
        }
    });
    return response.json();
}
```

## 🚨 Gestion des erreurs

### Codes d'erreur WebSocket
- **4000** : Erreur serveur générale
- **4001** : Token JWT invalide

### Erreurs HTTP
- **404** : Utilisateur ou message non trouvé
- **403** : Action non autorisée (modification/suppression)
- **401** : Token manquant ou invalide

## 🔒 Sécurité

- Authentification JWT obligatoire
- Validation des permissions (propriétaire pour modification/suppression)
- Vérification de l'existence des destinataires
- Nettoyage automatique des connexions fermées
- Blacklist des tokens pour déconnexion sécurisée

## 📊 Performances

- Connexions WebSocket persistantes
- Diffusion optimisée aux participants uniquement
- Index sur les tokens blacklistés
- Nettoyage automatique des connexions mortes
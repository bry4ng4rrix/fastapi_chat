# API de Messagerie en Temps Réel 

Une API FastAPI complète pour un système de messagerie en temps réel avec WebSocket et authentification JWT.

## 📋 Fonctionnalités

- 💬 **Messagerie en temps réel** avec WebSocket
- 🔐 **Authentification JWT** sécurisée
- 👥 **Gestion des utilisateurs** avec CRUD complet
- 📨 **Conversations privées** entre utilisateurs
- 🟢 **Statut en ligne** des utilisateurs connectés
- 🚫 **Blacklist de tokens** pour la déconnexion sécurisée
- 📊 **Activité utilisateurs** en temps réel

## 🛠️ Installation et Configuration

### Prérequis

- **Python 3.8+**
- **SQLite** (inclus avec Python)
- **Git** (pour cloner le projet)

### 1. Cloner le Projet

```bash
git clone https://github.com/bry4ng4rrix/fastapi_chat.git
cd fastapi_chat
```

### 2. Créer un Environnement Virtuel

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les Dépendances

```bash
pip install -r requirements.txt
```

### 4. Lancement de l'Application

#### Développement
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Vérification de l'Installation

Ouvrez votre navigateur et allez à :

- **Documentation API** : http://localhost:8000/docs
- **API Alternative** : http://localhost:8000/redoc

## 🏗️ Architecture

### Modèles de Données

#### User (Utilisateur)
```python
class User(SQLModel, table=True):
    id: Optional[int]           # Clé primaire
    name: str                   # Nom (max 50 caractères)
    email: str                  # Email unique (max 100 caractères)
    password: str               # Mot de passe hashé (max 100 caractères)
    created_at: datetime        # Date de création
    updated_at: datetime        # Date de mise à jour
```

#### Message (Message)
```python
class Message(SQLModel, table=True):
    id: Optional[int]           # Clé primaire
    content: str                # Contenu du message
    created_at: datetime        # Horodatage (UTC)
    updated_at: Optional[datetime] # Date de modification
    sender_id: int              # ID de l'expéditeur
    receiver_id: Optional[int]  # ID du destinataire (None = message public)
```

#### TokenBlacklist (Blacklist de Tokens)
```python
class TokenBlacklist(SQLModel, table=True):
    id: Optional[int]           # Clé primaire
    token: str                  # Token JWT blacklisté (unique)
    blacklisted_at: datetime    # Date de blacklistage
```

## 🚀 API Endpoints

### 🔐 Authentification (`/auth`)

| Méthode | Endpoint | Description | Auth | Body | Réponse |
|---------|----------|-------------|------|------|---------|
| `POST` | `/auth/register` | Créer un compte utilisateur | ❌ | `{"name": "Jean", "email": "jean@ex.com", "password": "pass123"}` | `UserRead` |
| `POST` | `/auth/token` | Connexion et récupération token JWT | ❌ | Form: `username=email&password=pass` | `{"access_token": "jwt...", "token_type": "bearer"}` |
| `GET` | `/auth/me` | Informations utilisateur connecté | ✅ | - | `UserRead` |
| `POST` | `/auth/logout` | Déconnexion avec blacklist token | ✅ | - | `{"message": "Successfully logged out"}` |
| `POST` | `/auth/refresh` | Renouveler le token JWT | ✅ | - | `{"access_token": "jwt...", "token_type": "bearer"}` |

### 👥 Gestion Utilisateurs (`/user`)

| Méthode | Endpoint | Description | Auth | Body | Réponse |
|---------|----------|-------------|------|------|---------|
| `POST` | `/user/` | Créer un utilisateur (Admin) | ✅ | `{"name": "Marie", "email": "marie@ex.com", "password": "pass456"}` | `UserRead` |
| `GET` | `/user/` | Liste tous les utilisateurs | ✅ | - | `List[UserRead]` |
| `GET` | `/user/{user_id}` | Détails d'un utilisateur | ✅ | - | `UserRead` |
| `PUT` | `/user/me` | Modifier son profil | ✅ | `{"name": "Nouveau nom", "email": "nouveau@ex.com"}` | `UserRead` |
| `GET` | `/user/active/list` | Utilisateurs en ligne | ✅ | - | `{"active_users": [1,3,5], "count": 3, "timestamp": "..."}` |
| `GET` | `/user/active/status/{user_id}` | Statut d'activité utilisateur | ✅ | - | `{"user_id": 3, "is_active": true, "timestamp": "..."}` |
| `POST` | `/user/broadcast` | Diffusion message à tous | ✅ | `{"message": "Annonce importante"}` | `{"status": "Message diffusé", "recipients": 12}` |

### 💬 Messages (`/message`)

| Méthode | Endpoint | Description | Auth | Body | Réponse |
|---------|----------|-------------|------|------|---------|
| `POST` | `/message/` | Envoyer un message privé | ✅ | Form: `receiver_id=2&content=Bonjour` | `Message` |
| `GET` | `/message/` | Tous mes messages | ✅ | - | `List[Message]` |
| `GET` | `/message/conversation/{user_id}` | Conversation avec utilisateur | ✅ | - | `List[Message]` |
| `PUT` | `/message/{message_id}` | Modifier un message | ✅ | Form: `content=Message modifié` | `Message` |
| `DELETE` | `/message/{message_id}` | Supprimer un message | ✅ | - | `{"message": "Message supprimé avec succès"}` |
| `GET` | `/message/online-users` | Utilisateurs connectés chat | ✅ | - | `List[int]` |

### 🔌 WebSocket Endpoints

| Type | Endpoint | Description | Auth | Protocole |
|------|----------|-------------|------|-----------|
| WS | `/user/ws/{token}` | Connexion activité utilisateurs | ✅ | WebSocket |
| WS | `/message/ws?token={token}` | Connexion messagerie temps réel | ✅ | WebSocket |

### 📊 Codes de Réponse HTTP

| Code | Signification | Cas d'usage |
|------|---------------|-------------|
| `200` | Succès | Opération réussie |
| `201` | Créé | Ressource créée avec succès |
| `400` | Requête invalide | Email déjà existant, données manquantes |
| `401` | Non autorisé | Token invalide/expiré, mauvais identifiants |
| `403` | Interdit | Pas d'autorisation pour cette action |
| `404` | Non trouvé | Utilisateur/Message introuvable |
| `422` | Données invalides | Format JSON incorrect |

## 🔌 WebSocket

### Connexion Activité Utilisateurs
```
ws://localhost:8000/user/ws/<jwt_token>
```

### Connexion Messages Chat
```
ws://localhost:8000/message/ws?token=<jwt_token>
```

### Messages WebSocket

#### Ping/Pong (Maintien de connexion)
```json
// Client → Serveur
{"type": "ping"}

// Serveur → Client
{"type": "pong", "timestamp": "2025-09-15T10:30:00Z"}
```

#### Activité utilisateur
```json
// Client → Serveur
{"type": "activity_update"}

// Serveur → Tous les autres clients
{
  "type": "user_status",
  "user_id": 1,
  "status": "online",
  "timestamp": "2025-09-15T10:30:00Z"
}
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

**Utilisateurs actifs :**
```json
{
  "type": "active_users",
  "users": [1, 2, 3, 5],
  "timestamp": "2025-09-15T10:30:00Z"
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
- **Diffusion ciblée** des messages aux participants
- **Gestion des erreurs** et reconnexions
- **Suivi d'activité** en temps réel

## 📝 Exemples d'Utilisation

### Client JavaScript WebSocket Complet
```javascript
class GarrixClient {
    constructor(apiUrl, token) {
        this.apiUrl = apiUrl;
        this.token = token;
        this.activityWs = null;
        this.messageWs = null;
        this.activeUsers = new Set();
    }

    // Connexion pour le suivi d'activité
    connectActivity() {
        this.activityWs = new WebSocket(`${this.apiUrl}/user/ws/${this.token}`);
        
        this.activityWs.onopen = () => {
            console.log('🟢 Connexion activité établie');
            this.startActivityPing();
        };
        
        this.activityWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleActivityMessage(data);
        };
    }

    // Connexion pour les messages
    connectMessages() {
        this.messageWs = new WebSocket(`${this.apiUrl}/message/ws?token=${this.token}`);
        
        this.messageWs.onopen = () => {
            console.log('💬 Connexion messages établie');
        };
        
        this.messageWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
    }

    startActivityPing() {
        setInterval(() => {
            if (this.activityWs?.readyState === WebSocket.OPEN) {
                this.activityWs.send(JSON.stringify({type: 'ping'}));
            }
        }, 30000);
    }

    handleActivityMessage(data) {
        switch(data.type) {
            case 'active_users':
                this.activeUsers = new Set(data.users);
                this.onActiveUsersUpdate(Array.from(this.activeUsers));
                break;
            case 'user_status':
                if (data.status === 'online') {
                    this.activeUsers.add(data.user_id);
                } else {
                    this.activeUsers.delete(data.user_id);
                }
                this.onUserStatusChange(data.user_id, data.status);
                break;
        }
    }

    handleMessage(data) {
        switch(data.type) {
            case 'new_message':
                this.onNewMessage(data);
                break;
            case 'message_updated':
                this.onMessageUpdated(data);
                break;
            case 'message_deleted':
                this.onMessageDeleted(data.id);
                break;
        }
    }

    sendMessage(receiverId, content) {
        if (this.messageWs?.readyState === WebSocket.OPEN) {
            this.messageWs.send(JSON.stringify({
                type: 'send_message',
                receiver_id: receiverId,
                content: content
            }));
        }
    }

    // Callbacks à implémenter
    onActiveUsersUpdate(users) { console.log('Utilisateurs actifs:', users); }
    onUserStatusChange(userId, status) { console.log(`${userId} est ${status}`); }
    onNewMessage(message) { console.log('Nouveau message:', message); }
    onMessageUpdated(message) { console.log('Message modifié:', message); }
    onMessageDeleted(messageId) { console.log('Message supprimé:', messageId); }
}

// Utilisation
const client = new GarrixClient('ws://localhost:8000', 'your-jwt-token');
client.connectActivity();
client.connectMessages();
```

### Client HTTP avec Authentification
```javascript
class GarrixAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.token = localStorage.getItem('user_token');
    }

    async login(email, password) {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        
        const response = await fetch(`${this.baseUrl}/auth/token`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('user_token', this.token);
            return data;
        }
        throw new Error('Échec de la connexion');
    }

    async getConversation(userId) {
        const response = await fetch(`${this.baseUrl}/message/conversation/${userId}`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        return response.json();
    }

    async sendMessage(receiverId, content) {
        const formData = new FormData();
        formData.append('receiver_id', receiverId);
        formData.append('content', content);
        
        const response = await fetch(`${this.baseUrl}/message/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${this.token}` },
            body: formData
        });
        return response.json();
    }

    async getActiveUsers() {
        const response = await fetch(`${this.baseUrl}/user/active/list`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        return response.json();
    }
}

// Utilisation
const api = new GarrixAPI('http://localhost:8000');
```

## 📚 Documentation

- **FastAPI Docs** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **Code Source** : Commenté et documenté
- **API Reference** : Générée automatiquement par FastAPI

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/nouvelle-fonctionnalité`)
3. Commit vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalité`)
5. Créez une Pull Request

## 🆘 Support

Pour obtenir de l'aide :

1. Consultez la documentation intégrée
2. Vérifiez les issues GitHub existantes
<<<<<<< HEAD
3. Créez une nouvelle issue si nécessaire
=======
3. Créez une nouvelle issue si nécessaire
>>>>>>> a15f7b9 (w)

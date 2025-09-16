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

### 9. Vérification de l'Installation

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

## 🚀 Endpoints API

### Authentification

#### `POST /auth/register`
Inscription d'un nouvel utilisateur
```json
{
  "name": "Jean Dupont",
  "email": "jean@example.com",
  "password": "motdepasse123"
}
```

#### `POST /auth/token`
Connexion et récupération du token JWT
```form-data
username=jean@example.com
password=motdepasse123
```

#### `POST /auth/logout`
Déconnexion et blacklistage du token
```http
Authorization: Bearer <token>
```

#### `GET /auth/me`
Informations de l'utilisateur connecté
```http
Authorization: Bearer <token>
```

### Utilisateurs

#### `GET /users/`
Liste de tous les utilisateurs
```http
Authorization: Bearer <token>
```

#### `GET /users/me`
Profil de l'utilisateur connecté
```http
Authorization: Bearer <token>
```

#### `GET /users/active/list`
Liste des utilisateurs actuellement en ligne
```http
Authorization: Bearer <token>
```

#### `GET /users/active/status/{user_id}`
Vérifier si un utilisateur est en ligne
```http
Authorization: Bearer <token>
```

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

#### `POST /users/broadcast`
Diffuse un message à tous les utilisateurs connectés
```json
{
  "message": "Annonce importante à tous les utilisateurs"
}
```

## 🔌 WebSocket

### Connexion Utilisateurs (Activité)
```
ws://localhost:8000/users/ws/<jwt_token>
```

### Connexion Messages (Chat)
```
ws://localhost:8000/messages/ws?token=<jwt_token>
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
        this.activityWs = new WebSocket(`${this.apiUrl}/users/ws/${this.token}`);
        
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
        this.messageWs = new WebSocket(`${this.apiUrl}/messages/ws?token=${this.token}`);
        
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
        const response = await fetch(`${this.baseUrl}/messages/conversation/${userId}`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        return response.json();
    }

    async sendMessage(receiverId, content) {
        const formData = new FormData();
        formData.append('receiver_id', receiverId);
        formData.append('content', content);
        
        const response = await fetch(`${this.baseUrl}/messages/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${this.token}` },
            body: formData
        });
        return response.json();
    }

    async getActiveUsers() {
        const response = await fetch(`${this.baseUrl}/users/active/list`, {
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
3. Créez une nouvelle issue si nécessaire

---

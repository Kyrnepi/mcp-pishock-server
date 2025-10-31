
# MCP PiShock Server

**English** | [Français](#serveur-mcp-pishock-français)

---

## English

HTTP streamable MCP (Model Context Protocol) server for controlling PiShock devices via their REST API.

### Features

- **SHOCK**: Activates electric shock function with duration (1-15s) and intensity (1-100)
- **VIBRATE**: Activates vibration function with duration and intensity (1-100)  
- **BEEP**: Activates beep sound function with duration
- **Authentication**: Bearer token protection
- **MCP Protocol**: Full MCP 2025-06-18 protocol support with tool discovery
- **Docker**: Containerized with environment variable configuration

### Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Fill in the environment variables in `.env`:
```bash
PISHOCK_USERNAME=your_username
PISHOCK_APIKEY=your_api_key
PISHOCK_CODE=your_share_code
MCP_AUTH_TOKEN=secure_random_token
SCRIPT_NAME=MCP_Server
```

#### Getting PiShock Credentials

1. Create an account on [PiShock.com](https://pishock.com)
2. In the Account section:
   - Get your **Username**
   - Generate an **API Key**
   - Create a **Share Code** with desired limitations

### Deployment

#### With Docker Compose (recommended)

```bash
docker-compose up -d
```

#### With Docker

```bash
docker build -t pishock-mcp-server .
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name pishock-mcp-server \
  pishock-mcp-server
```

#### Local Development

```bash
pip install -r requirements.txt
python app.py
```

### MCP Client Usage

The server implements the full MCP protocol. MCP clients will automatically:

1. **Initialize** with the server using the `initialize` method
2. **Discover tools** using `tools/list` to see available SHOCK, VIBRATE, BEEP functions
3. **Call tools** using `tools/call` with the appropriate parameters

#### Authentication

All requests require a Bearer token in the Authorization header:
```
Authorization: Bearer YOUR_MCP_AUTH_TOKEN
```

#### Available Tools

- **SHOCK**: `{"name": "SHOCK", "arguments": {"duration": 2, "intensity": 10}}`
- **VIBRATE**: `{"name": "VIBRATE", "arguments": {"duration": 3, "intensity": 50}}`
- **BEEP**: `{"name": "BEEP", "arguments": {"duration": 1}}`

### Direct API Usage (Compatibility)

For non-MCP clients, direct endpoints are available:

```bash
# Shock
curl -X POST "http://localhost:8000/mcp/SHOCK" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"duration": 1, "intensity": 5}'

# Vibrate
curl -X POST "http://localhost:8000/mcp/VIBRATE" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"duration": 2, "intensity": 30}'

# Beep
curl -X POST "http://localhost:8000/mcp/BEEP" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"duration": 1}'
```

### Monitoring

- **Health Check**: `GET /health`
- **API Documentation**: `http://localhost:8000/docs`
- **MCP Info**: `GET /mcp`
- **Logs**: `docker-compose logs -f`

### Security

⚠️ **WARNING**: Shock devices are not designed for human use and can cause serious injury including cardiac events. Never use near the heart or if you have heart conditions.

- Use strong authentication tokens
- Limit network access to the server
- Configure appropriate limits in PiShock
- Monitor usage logs

### Limitations

- Shock duration: 1-15 seconds (PiShock API limit)
- Intensity: 1-100 (PiShock API limit)
- One command at a time per share code
- Device must be online and connected

---

## Serveur MCP PiShock (Français)

Serveur MCP (Model Context Protocol) HTTP streamable pour contrôler les dispositifs PiShock via leur API REST.

### Fonctionnalités

- **SHOCK**: Active la fonction de choc électrique avec durée (1-15s) et intensité (1-100)
- **VIBRATE**: Active la fonction de vibration avec durée et intensité (1-100)  
- **BEEP**: Active la fonction de bip sonore avec durée
- **Authentification**: Protection par token Bearer
- **Protocole MCP**: Support complet du protocole MCP 2025-06-18 avec découverte d'outils
- **Docker**: Containerisé avec toutes les variables d'environnement

### Configuration

1. Copiez `.env.example` vers `.env`:
```bash
cp .env.example .env
```

2. Remplissez les variables d'environnement dans `.env`:
```bash
PISHOCK_USERNAME=votre_nom_utilisateur
PISHOCK_APIKEY=votre_cle_api
PISHOCK_CODE=votre_code_partage
MCP_AUTH_TOKEN=un_token_securise_aleatoire
SCRIPT_NAME=MCP_Server
```

#### Obtenir les identifiants PiShock

1. Créez un compte sur [PiShock.com](https://pishock.com)
2. Dans la section Account :
   - Récupérez votre **Username**
   - Générez une **API Key**
   - Créez un **Share Code** avec les limitations désirées

### Déploiement

#### Avec Docker Compose (recommandé)

```bash
docker-compose up -d
```

#### Avec Docker

```bash
docker build -t pishock-mcp-server .
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name pishock-mcp-server \
  pishock-mcp-server
```

#### Développement local

```bash
pip install -r requirements.txt
python app.py
```

### Utilisation avec un client MCP

Le serveur implémente le protocole MCP complet. Les clients MCP vont automatiquement :

1. **S'initialiser** avec le serveur via la méthode `initialize`
2. **Découvrir les outils** via `tools/list` pour voir les fonctions SHOCK, VIBRATE, BEEP disponibles
3. **Appeler les outils** via `tools/call` avec les paramètres appropriés

#### Authentification

Toutes les requêtes nécessitent un token Bearer dans l'header Authorization :
```
Authorization: Bearer YOUR_MCP_AUTH_TOKEN
```

#### Outils disponibles

- **SHOCK**: `{"name": "SHOCK", "arguments": {"duration": 2, "intensity": 10}}`
- **VIBRATE**: `{"name": "VIBRATE", "arguments": {"duration": 3, "intensity": 50}}`
- **BEEP**: `{"name": "BEEP", "arguments": {"duration": 1}}`

### Utilisation API directe (Compatibilité)

Pour les clients non-MCP, des endpoints directs sont disponibles :

```bash
# Shock
curl -X POST "http://localhost:8000/mcp/SHOCK" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"duration": 1, "intensity": 5}'

# Vibrate
curl -X POST "http://localhost:8000/mcp/VIBRATE" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"duration": 2, "intensity": 30}'

# Beep
curl -X POST "http://localhost:8000/mcp/BEEP" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"duration": 1}'
```

### Surveillance

- **Health Check**: `GET /health`
- **Documentation API**: `http://localhost:8000/docs`
- **Informations MCP**: `GET /mcp`
- **Logs**: `docker-compose logs -f`

### Sécurité

⚠️ **AVERTISSEMENT**: Les dispositifs de choc ne sont pas conçus pour un usage humain et peuvent causer des blessures graves y compris des événements cardiaques. Ne jamais utiliser près du cœur ou si vous avez des problèmes cardiaques.

- Utilisez des tokens d'authentification forts
- Limitez l'accès réseau au serveur
- Configurez des limites appropriées dans PiShock
- Surveillez les logs d'utilisation

### Limitations

- Durée de choc : 1-15 secondes (limite API PiShock)
- Intensité : 1-100 (limite API PiShock) 
- Une seule commande à la fois par share code
- Le dispositif doit être en ligne et connecté
